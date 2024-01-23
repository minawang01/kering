import os
import pyodbc, struct
from azure import identity

from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

class ReturnItem(BaseModel):
    id: int
    sku: Union[str, None] = None
    image_link: Union[str, None] = None
    is_damaged: Union[bool, None] = None
    damage_type: Union[str, None] = None
    item_type: Union[str, None] = None
    
    
connection_string = os.environ["AZURE_SQL_CONNECTIONSTRING"]

app = FastAPI()

@app.get("/")
def root():
    print("Root of ReturnItem API")
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # Table should be created ahead of time in production app.
        cursor.execute("""
            CREATE TABLE ReturnItem (
                ID int NOT NULL PRIMARY KEY IDENTITY,
                SKU varchar(255),
                ImageLink varchar(255),
                IsDamaged varchar(255),
                DamageType varchar(255),
                ItemType varchar(255)
            );
        """)

        conn.commit()
    except Exception as e:
        # Table may already exist
        print(e)
    return "ReturnItem API"

@app.get("/all")
def get_returns():
    rows = []
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ReturnItem")

        for row in cursor.fetchall():
            print(row.ItemType, row.SKU, row.ImageLink, row.IsDamaged, row.DamageType)
            rows.append(f"{row.ItemType}, {row.SKU}, {row.ImageLink}, {row.IsDamaged}, {row.DamageType}")
    return rows

@app.post("/item")
def create_item(item: ReturnItem):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO ReturnItem (SKU, ImageLink, IsDamaged, DamageType, ItemType) VALUES (?, ?, ?, ?, ?)", item.sku, item.image_link, item.is_damaged, item.damage_type, item.item_type)
        conn.commit()

    return item

def get_conn():
    credential = identity.DefaultAzureCredential(exclude_interactive_browser_credential=False)
    token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
    conn = pyodbc.connect(connection_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
    return conn