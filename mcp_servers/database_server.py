# Mocking database below you can have your db as well.
import random
import os
import asyncio
import json
from datetime import datetime,timedelta
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool,TextContent
Customers={
        "user@email.com": {
            "ID": "C001",
            "Name": "John Doe",
            "Email": "user@email.com",
            "Plan": "Premium",
            "Since": "2024-01-15",
            "Status": "Active"
        },
        "jane@example.com": {
            "ID": "C002",
            "Name": "Jane Smith",
            "Email": "jane@example.com",
            "Plan": "Basic",
            "Since": "2024-06-20",
            "Status": "Active"
        },
        "test@test.com": {
            "ID": "C003",
            "Name": "Test User",
            "Email": "test@test.com",
            "Plan": "Trial",
            "Since": "2024-12-01",
            "Status": "Trial"
        }
    }

Orders= {
        "C001": [
            {
                "OrderID": "ORD-45231",
                "Amount": 29.99,
                "Date": "2024-12-20",
                "Status": "Complete",
                "Item": "Premium Monthly"
            },
            {
                "OrderID": "ORD-45232",
                "Amount": 29.99,
                "Date": "2024-12-20",
                "Status": "Complete",
                "Item": "Premium Monthly"
            },
            {
                "OrderID": "ORD-44100",
                "Amount": 29.99,
                "Date": "2024-11-20",
                "Status": "Completed",
                "Item": "Premium Monthly"
            }
        ],
        "C002": [
            {
                "OrderID": "ORD-43001",
                "Amount": 9.99,
                "Date": "2024-12-20",
                "Status": "Completed",
                "Item": "Basic Monthly"
            }
        ],
        "C003": [
            {
                "OrderID": "ORD-5001",
                "Amount": 0.00,
                "Date": "2024-12-01",
                "Status": "Completed",
                "Item": "Free Trial",
                "Reference": ""
            }
        ]
    }

Refunds=[]


# Below are the database functions/Tools


def get_customer(email:str):
    """Look up a customer by email"""
    
    Customer=Customers.get(email.lower())
    if Customer:
        return {
            "success":True,
            "customer":Customer
        }
    return {
            "success":False,
            "customer":f'Customer not found : {email}'
        }
def get_orders(customer_id:str):
    """Get order history for customer"""
    
    orders=Orders.get(customer_id,[])
    return{
        "success":True,
        "customer_id":customer_id,
        "total_orders":len(orders),
        "orders":orders
    }
    
def find_duplicate_charges(customer_id:str):
    orders=Orders.get(customer_id,[])
    
    charges_by_date ={}
    for order in orders:
        key = f'{order["date"]}_{order["amount"]}'
        if key not in charges_by_date:
            charges_by_date[key]=[]
        charges_by_date[key].append(order)
        
    duplicate=[]
    
    for key,group in charges_by_date.items():
        if len(group)>1:
            duplicate.extend(group[1:])
            
    if duplicate:
        return{
            "success":True,
            "found_duplicates": True,
            "duplicates_count":len(duplicate),
            "duplicates":duplicate,
            "total_refund_amount":sum(d['amount'] for d in duplicate)
        }
    return {
        "success":False,
        "found_duplicates": False,
        "message":"No duplicate charges found"
    }
    
def process_refund(order_id:str,amount:float,reason:str = "duplicate_charges"):
    for refund in Refunds:
        if refund['order_id']==order_id:
            return{
                "success":False,
                "error":f"Order {order_id} has already been refunded"
            }
    refund={
        "refund_id":f'REF-{random.randint(10000,99999)}',
        "order_id":order_id,
        "amount":amount,
        "reason":reason,
        "status":"initiated",
        "process_at": datetime.now().isoformat(),
        "estimated_completion":(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    }
    Refunds.append(refund)
    
    return {
        "success":True,
        "refund":refund,
        "message":f"Refund of ${amount:.2f} initiated for order {order_id}"
    }
    
def get_subscription(customer_id:str):
    customer=None
    for email,data in Customers.items():
        if data["id"]==customer_id:
            customer=data
            break
        
    if not customer:
        return {"success":False,"error":"Customer not found"}
    
    return {
        "success":True,
        "customer_id":customer_id,
        "plan":customer['plan'],
        "status":customer['status'],
        'member_since': customer['since'],
        'nex_billing_date':(datetime.now()+timedelta(days=30)).strftime("%Y-%m-%d")
    }
    
    
    #setting up mcp server
    
mcp_server=Server("mock-database-server")

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_customer",
            description="Lookup a customer by email address. Returns customer profile including name, plan, and account status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Customer email address"
                    }
                },
                "required": ["email"]
            }
        ),
        Tool(
            name="get_orders",
            description="Get order history for a customer by their customer ID. Returns list of all orders with date, amount, and status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID",
                        "example": "C001"
                    }
                },
                "required": ["customer_id"]
            }
        ),
        Tool(
            name="find_duplicate_charges",
            description="Find duplicate charges for a customer. Identifies orders with the same amount on the same date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID to check for duplicates"
                    }
                },
                "required": ["customer_id"]
            }
        ),
        Tool(
            name="process_refund",
            description="Process a refund for a specific order. Creates a refund record and initiates the refund process.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID to refund",
                        "example": "ORD-45231"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to refund in dollars"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for the refund",
                        "example": "Duplicate charge",
                        "default": "Duplicate charge"
                    }
                },
                "required": ["order_id", "amount"]
            }
        ),
        Tool(
            name="subscription_status",
            description="Get subscription details for a customer including plan type, status, and next billing date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Customer ID"
                    }
                },
                "required": ["customer_id"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name:str,arguments:dict[str,Any])->list[TextContent]:
    """Handel Tool calls"""
    
    if name=="get_customer":
        result=get_customer(arguments['email'])
    elif name == "get_orders":
        result=get_orders(arguments['customer_id'])
    elif name == "find_duplicate_charges":
        result=find_duplicate_charges(arguments['customer_id'])
    elif name=='process_refund':
        result=process_refund(
            arguments['order_id'],
            arguments['amount'],
            arguments.get('reason','duplicate_charge')
        )
    elif name=="get_subscription":
        result=get_subscription(arguments["customer_id"])
    else:
        result={'error':f'unkonwn tool : {name}'}
        
    return [TextContent(type='text',text=json.dumps(result,indent=2))]

async def main():
    """Run the mcp server over stdio"""
    
    import sys
    print("starting Mock database MCP server (STDIO)",file=sys.stderr)
    
    async with stdio_server() as (read_stream,write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )
if __name__=='__main__':
    asyncio.run(main())