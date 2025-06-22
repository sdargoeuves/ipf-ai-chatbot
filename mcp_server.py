from mcp.server.fastmcp import FastMCP
from ipfabric import IPFClient
import os
import json
from typing import Optional, Dict, Any, List

mcp = FastMCP("IPFabric", log_level="DEBUG")
ipf = None

@mcp.tool()
def ipf_get_snapshots():
    """
    Get all available snapshots from IP Fabric
    
    Returns:
        List of snapshots with their details
    """
    try:
        snapshots = ipf.get_snapshots()
        return {"snapshots": snapshots, "current_snapshot": ipf.snapshot_id}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def ipf_get_devices(filters: Optional[Dict[str, Any]] = None, columns: Optional[List[str]] = None):
    """
    Get devices from IP Fabric inventory
    
    Args:
        filters: Optional dict of filters to apply (e.g. {"hostname": "router1"})
        columns: Optional list of specific columns to return
    
    Returns:
        Device inventory data
    """
    try:
        # Use the SDK's inventory.devices method
        result = ipf.inventory.devices.all(
            filters=filters or {},
            columns=columns
        )
        return result
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve devices"}

@mcp.tool()
def ipf_get_interfaces(filters: Optional[Dict[str, Any]] = None, columns: Optional[List[str]] = None):
    """
    Get interfaces from IP Fabric inventory
    
    Args:
        filters: Optional dict of filters to apply (e.g. {"hostname": "router1"})
        columns: Optional list of specific columns to return
    
    Returns:
        Interface inventory data
    """
    try:
        result = ipf.inventory.interfaces.all(
            filters=filters or {},
            columns=columns
        )
        return result
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve interfaces"}

@mcp.tool()
def ipf_get_sites(filters: Optional[Dict[str, Any]] = None, columns: Optional[List[str]] = None):
    """
    Get sites from IP Fabric inventory
    
    Args:
        filters: Optional dict of filters to apply
        columns: Optional list of specific columns to return
    
    Returns:
        Sites inventory data
    """
    try:
        result = ipf.inventory.sites.all(
            filters=filters or {},
            columns=columns
        )
        return result
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve sites"}

@mcp.tool()
def ipf_get_vendors(filters: Optional[Dict[str, Any]] = None, columns: Optional[List[str]] = None):
    """
    Get vendors from IP Fabric inventory
    
    Args:
        filters: Optional dict of filters to apply
        columns: Optional list of specific columns to return
    
    Returns:
        Vendors inventory data
    """
    try:
        result = ipf.inventory.vendors.all(
            filters=filters or {},
            columns=columns
        )
        return result
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve vendors"}

@mcp.tool()
def ipf_get_platforms(filters: Optional[Dict[str, Any]] = None, columns: Optional[List[str]] = None):
    """
    Get platforms from IP Fabric inventory
    
    Args:
        filters: Optional dict of filters to apply
        columns: Optional list of specific columns to return
    
    Returns:
        Platforms inventory data
    """
    try:
        result = ipf.inventory.platforms.all(
            filters=filters or {},
            columns=columns
        )
        return result
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve platforms"}

@mcp.tool()
def ipf_get_routing_table(filters: Optional[Dict[str, Any]] = None, columns: Optional[List[str]] = None):
    """
    Get routing table data from IP Fabric
    
    Args:
        filters: Optional dict of filters to apply
        columns: Optional list of specific columns to return
    
    Returns:
        Routing table data
    """
    try:
        result = ipf.technology.routing.routes.all(
            filters=filters or {},
            columns=columns
        )
        return result
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve routing table"}

@mcp.tool()
def ipf_get_vlans(filters: Optional[Dict[str, Any]] = None, columns: Optional[List[str]] = None):
    """
    Get VLAN data from IP Fabric
    
    Args:
        filters: Optional dict of filters to apply
        columns: Optional list of specific columns to return
    
    Returns:
        VLAN data
    """
    try:
        result = ipf.technology.vlans.device_detail.all(
            filters=filters or {},
            columns=columns
        )
        return result
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve VLANs"}

@mcp.tool()
def ipf_get_neighbors(filters: Optional[Dict[str, Any]] = None, columns: Optional[List[str]] = None):
    """
    Get neighbor discovery data from IP Fabric
    
    Args:
        filters: Optional dict of filters to apply
        columns: Optional list of specific columns to return
    
    Returns:
        Neighbor discovery data
    """
    try:
        result = ipf.technology.neighbors.detail.all(
            filters=filters or {},
            columns=columns
        )
        return result
    except Exception as e:
        return {"error": str(e), "message": "Failed to retrieve neighbors"}

@mcp.tool()
def ipf_get_available_columns(table_type: str):
    """
    Get available columns for a specific table type
    
    Args:
        table_type: Type of table (e.g., "devices", "interfaces", "routing", "vlans")
    
    Returns:
        List of available columns for the specified table
    """
    try:
        table_map = {
            "devices": ipf.inventory.devices,
            "interfaces": ipf.inventory.interfaces,
            "sites": ipf.inventory.sites,
            "vendors": ipf.inventory.vendors,
            "platforms": ipf.inventory.platforms,
            "routing": ipf.technology.routing.routes,
            "vlans": ipf.technology.vlans.device_detail,
            "neighbors": ipf.technology.neighbors.detail,
        }
        
        if table_type not in table_map:
            return {"error": f"Unknown table type: {table_type}", "available_types": list(table_map.keys())}
        
        columns = ipf.get_columns(table_map[table_type])
        return {"table_type": table_type, "columns": columns}
    except Exception as e:
        return {"error": str(e), "message": f"Failed to get columns for {table_type}"}

@mcp.tool()
def ipf_get_connection_info():
    """
    Get IP Fabric connection information and status
    
    Returns:
        Connection details and current snapshot info
    """
    try:
        snapshots = ipf.get_snapshots()
        current_snapshot = ipf.snapshot_id
        
        return {
            "base_url": ipf.base_url,
            "current_snapshot_id": current_snapshot,
            "available_snapshots": len(snapshots) if snapshots else 0,
            "api_version": ipf.api_version,
            "os_version": ipf.os_version
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to get connection info"}

@mcp.tool()
def ipf_set_snapshot(snapshot_id: str):
    """
    Set the active snapshot for queries
    
    Args:
        snapshot_id: The snapshot ID to set as active
    
    Returns:
        Confirmation of snapshot change
    """
    try:
        old_snapshot = ipf.snapshot_id
        ipf.snapshot_id = snapshot_id
        return {
            "success": True,
            "old_snapshot": old_snapshot,
            "new_snapshot": ipf.snapshot_id,
            "message": f"Successfully changed snapshot from {old_snapshot} to {snapshot_id}"
        }
    except Exception as e:
        return {"error": str(e), "message": f"Failed to set snapshot to {snapshot_id}"}

if __name__ == "__main__":
    # Load IP Fabric configuration from environment variables
    ipf_url = os.getenv("IPF_URL")
    ipf_token = os.getenv("IPF_TOKEN")
    ipf_snapshot = os.getenv("IPF_SNAPSHOT")  # Optional - will use latest if not specified
    
    if not ipf_url or not ipf_token:
        raise ValueError("IPF_URL and IPF_TOKEN environment variables must be set")
    
    try:
        # Initialize IP Fabric client
        ipf = IPFClient(
            url=ipf_url, 
            token=ipf_token,
            snapshot_id=ipf_snapshot,  # Will use latest if None
            verify=False  # Set to True in production with proper certificates
        )
        
        # Test connection
        ipf_version = ipf.os_version
        print(f"Successfully connected to IP Fabric: {ipf.base_url} ({ipf.os_version})")
        print(f"Active snapshot: {ipf.snapshot_id}")
        
    except Exception as e:
        print(f"Failed to initialize IP Fabric client: {e}")
        raise
    
    mcp.run(transport="stdio")

