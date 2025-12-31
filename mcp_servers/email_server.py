import json
import asyncio
from datetime import datetime
from typing import Any
import random
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool,TextContent


EMAIL_LOG=[]

def send_email(to:str,subject:str,body:str)->dict:
    """Send Generic Email"""
    
    email_id=f'EMAIL-{random.randint(10000,99999)}'
    
    email_record={
        "email_id":email_id,
        "to":to,
        "subject":subject,
        "body":body,
        "sent_at":datetime.now().isoformat(),
        "status": "sent"
    }
    
    EMAIL_LOG.append(email_record)
    
    print(f'Email send to {to}: {subject}',file=sys.stderr)
    
    return {
        "success":True,
        "email_id":email_id,
        "message":f"Email sent to {to}",
        "subject":subject
    }
    
def send_password_reset(email:str)->dict:
    """Send a password reset email"""
    reset_token=f"RESET-{random.randint(10000,99999)}"
    reset_link=f"https://example.com/reset?token={reset_token}"
    
    subject="Password Reset Request"
    body=f"""
    Hello,
    You You requested password reset for your account.
    Click here to reset your password : {reset_link}
    This link expire in 24 hrs.
    If you didn't request this please ignore the email.
    
    Regards,
    Support Team
    """
    result=send_email(email,subject,body)
    result["reset_link"]=reset_link
    result['expires_in']="24 hours"
    
    return result

def send_refund_confirmation(email:str,refund_id:str,amount:float,order_id:str)->dict:
    """Send a request confirmation email"""
    
    subject=f"Refund Confirmed -${amount:.2f}"
    body=f"""
    Hello,
    Your refund has been processed successfully.
    
    Refund Details:
    -Refund ID:{refund_id}
    -Order ID:{order_id}
    -Amount: ${amount:.2f}
    -status : Initiated
    
    The refund will appear in your account in 3-5 working days.
    If you have any questions please reach out to our support team.
    
    Regards,
    Billing Team
    """
    
    result=send_email(email,subject,body)
    result['refund_id']=refund_id
    result['amount']=amount
    
    return result

def send_ticket_confirmation(email:str,ticket_id:str,issue_type:str)->dict:
    """Send a support ticket confirmation"""
    
    subject=f"Support Ticket Created - {ticket_id}"
    body=f"""
    Hello,
    
    Your support ticket has been created successfully.
    
    Ticket details:
    
    -Ticket ID : {ticket_id}
    -Issue Type:{issue_type}
    -Status: Open
    
    Our support team will respond within 24 hrs.
    
    Regards,
    Support Team
    """
    
    result=send_email(email,subject,body)
    result['ticket_id']=ticket_id
    
    return result


def get_email_history(email:str)->dict:
    """Get email history for an addresss"""
    emails =[e for e in EMAIL_LOG if e["to"]==email]
    
    return {
        "success":True,
        "email": email,
        "total_emails":len(emails),
        "emails":emails[-10:] #Last 10 emails
    }
    
    
mcp_server=Server("mock-email-server")

@mcp_server.list_tools()
async def list_tools()->list[Tool]:
    """List available emails tools"""
    return [
        Tool(
            name="send_email",
            description="Send generic email to receipt",
            inputSchema={
                "type":"object",
                "properties":{
                    "to":{
                        "type":"string",
                        "description":"Recipient email address"
                    },
                    "subject":{
                        "type":"string",
                        "description":"Email subject line"
                    },
                    "body":{
                        "type":"string",
                        "description":"Email body content"
                    }
                },
                "required":["to","subject","body"]
            }
        ),
        Tool(
            name="send_password_reset",
            description="Send a password reset email with secure reset link",
            inputSchema={
                "type":"object",
                "properties":{
                    "email":{
                        "type":"string",
                        "description":"User's email address"
                }
                },   
                "required":["email"]
            }
        ),
        Tool(
            name="send_refund_confirmation",
            description="send refund confirmation email with refund details",
            inputSchema={
                "type":"object",
                "properties":{
                    "email":{
                        "type":"string",
                        "description":"User's email address"
                },
                    "refund_id":{
                        "type":"string",
                        "description":"Refund ID"
                    },
                    "amount":{
                        "type":"number",
                        "description":"Refund amount in dollar"
                    },
                    "order_id":{
                        "type":"string",
                        "description":"Original order ID"
                }
                },
                "required":["email","refund_id","amount","order_id"]
            }
        ),
        Tool(
            name="send_ticket_confirmation",
            description="Send a support ticket confirmation email",
            inputSchema={
                "type":"object",
                "properties":{
                    "email":{
                        "type":"string",
                        "description":"User's email address"
                },
                    "tikect_id":{
                        "type":"string",
                        "description":"Support ticket ID"
                },
                    "issue_type":{
                        "type":"string",
                        "description":"Type of the issue (eg. billing,technical,general)"
                }
                },   
                "required":["email","ticket_id","issue_type"]
            }
        )
    ]
    
@mcp_server.call_tool()
async def call_tool(name:str,arguments:dict[str,Any])->list[TextContent]:
    """Handel tool calls"""
    
    if name == "send_email":
        result=send_email(
            arguments['to'],
            arguments['subject'],
            arguments['body'],
        )
    elif name=="send_password_reset":
        result=send_password_reset(arguments["email"])
    elif name == "send_refund_confirmation":
        result=send_refund_confirmation(
            arguments['email'],
            arguments['refund_id'],
            arguments['amount'],
            arguments['order_id'],
        )
        
    elif name=="send_ticket_confirmation":
        result=send_ticket_confirmation(
            arguments['email'],
            arguments['ticket_id'],
            arguments['issue_type'],
        )
    else:
        result={"error":f"Unkown tool : {name}"}
        
    return [TextContent(type="text",text=json.dumps(result,indent=2))]


async def main():
    """Run the MCP server over STDIO"""
    print("Starting Mock Email MCP server (STDIO)",file=sys.stderr)
    
    async with stdio_server() as (read_stream,write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )
        
if __name__=="__main__":
    asyncio.run(main())