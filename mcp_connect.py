"""
Mcp connection - this file handels connecting to mcp server using google adk

This module provide low level connection logic for:

STDIO MCP servers 
HTTP MCP servers

uses Google's ADK MCPToolSet for seamless integration

"""


import os
import sys
import asyncio
from typing import Any,Optional
from dataclasses import dataclass,field
from contextlib import AsyncExitStack

sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class MCPServerConfig:
    name:str
    type:str
    description:str=""
    enabled:bool=True
    
    # for STDIO servers
    command:str=""
    args:list[str]=field(default_factory=list)
    env:dict[str,str]=field(default_factory=dict)
    
    #for HTTP servers
    url:str=""
    
    
@dataclass
class MCPConnection:
    server:MCPServerConfig
    tool:list[Any]
    exit_stack:Optional[AsyncExitStack]=None
    connected:bool=False
    
async def connect_stdio_server(server:MCPServerConfig)->MCPConnection:
    """
    Connect to a STDIO Mcp server using Google Adk's MCPToolset.
    
    This spaws the server as a subprocess and communicates via STDIN/STDOUT
    
    Args:
        server:Server configuration from YAML
    Returns:
        MCPConnection with discovered tools
    
    """    
    
    try:
        from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
        from mcp import StdioServerParameters
        
        print(f'Connecting to STDIO server: {server.name}')
        print(f'commanf: {server.command} {''.join(server.args)}')
        
        env=os.environ.copy()
        env.update(server.env)
        
        stdio_params=StdioServerParameters(
            command=server.command,
            args=server.args,
            env=env
        )
        
        tools,exit_stack=await McpToolset.from_server(
            connection_parmas=stdio_params
        )
        
        print(f" Connected! Found {len(tools)} tools")
        
        for tool in tools:
            tool_name=getattr(tool,'name',getattr(tool,'__name__',str(tool)))
            print(f'  -{tool_name}')
            
        return MCPConnection(
            server=server,
            tool=list(tools),
            exit_stack=exit_stack,
            connected=True
        )
    except Exception as e:
        print(f"Connection Failed {str(e)}")
        return MCPConnection(server=server,tool=[],connected=False)
    
async def connect_http_server(server:MCPServerConfig)->MCPConnection:
    """
    Connect to an HTTP Mcp server using google ADk's MCPToolset
    
    Args:
        server:Server configuration with URL
    Returns:
        MCPConnection with discovered tools
    
    """ 
    
    try:
        from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
        
        print(f'Connecting to HTTP server: {server.name}')
        print(f'URL : {server.url}')
        
        tools,exit_stack=await McpToolset.from_server(
            connection_parmas={"url":server.url}
        )
        
        print(f" Connected! Found {len(tools)} tools")
        for tool in tools:
            tool_name=getattr(tool,'name',getattr(tool,'__name__',str(tool)))
            print(f'  -{tool_name}')
            
        return MCPConnection(
            server=server,
            tool=list(tools),
            exit_stack=exit_stack,
            connected=True
        )
    except Exception as e:
        print(f"Connection Failed {str(e)}")
        return MCPConnection(server=server,tool=[],connected=False)
    
async def connect_server(server:MCPServerConfig)->MCPConnection:
    """
    Connect to mcp server based on its type
    
    Args:
        server:Server configuration
    Returns:
        MCPConnection with tools
    
    """ 
    
    if not server.enabled:
        print(f"Skipping disabled servers : {server.name}")
        return MCPConnection(server=server,tool=[],connected=False)
    
    if server.type=='stdio':
        return await connect_stdio_server(server=server)
    elif server.type in ['http','stremable_http','sse']:
        return await connect_http_server(server)
    else:
        print(f"Unkonwn Server type: {server.type}")
        return MCPConnection(server=server,tool=[],connected=False)
    
async def disconnect_server(connection:MCPConnection)->None:
    """
    Disconnect from mcp server and cleanup resources.
    
    Args:
        connection: Active Mcp Connection
    
    """ 
    
    if connection.exit_stack:
        try:
            await connection.exit_stack.aclose()
            print(f"Disconnected from {connection.server.name}")
        except Exception as e:
            print(f"Error disconnecting: {e}")
            
    connection.connected=False
    

    
        
            
            
        
    
