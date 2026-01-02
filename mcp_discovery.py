"""
MCP Discovery reads mcp_config.yaml and discovers avilable mcp server.

this module handles:
Loading server configuration from yaml
parsing server definition
providing server metadata

The actual connection is handled by mcp_connect.py  
    
"""

import os
import sys
import yaml
from typing import Optional
from pathlib import Path

sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_connect import MCPServerConfig

def discover_servers(config_path:Optional[str]=None)->list[MCPServerConfig]:
    
    if config_path is None:
        config_path=Path(__file__).parent/"mcp_config.yaml"
    else:
        config_path=Path(config_path)
        
    if not config_path.exists():
        print(f"MCP config not found: {config_path}")
        return []
    
    print(f"Loading MCP config from : {config_path}")
    
    with open(config_path,"r") as f:
        config=yaml.safe_load(f)
        
    
    if not config:
        print("Empty config file")
        return []
    
    servers=[]
    
    for server_data in config.get("mcp_servers",[]):
        server=MCPServerConfig(
            name=server_data.get("name","unkown"),
            type=server_data.get("type","stdio"),
            description=server_data.get("description",""),
            enabled=server_data.get("enabled",True),
            command=server_data.get("command",""),
            args=server_data.get("args",[]),
            env=server_data.get("env",{}),
            url=server_data.get("url","")
        )
        servers.append(server)
        
    print(f'Found {len(servers)} MCP Servers: ')
    
    for s in servers:
        status="yes" if s.enabled else "no"
        print(f"{status} {s.name} ({s.type}):({s.description})")
        
    return server
        
    