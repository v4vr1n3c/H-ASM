def run_discovery(domain: str):
    # MVP mock: return a couple of assets to demonstrate flow.
    return [
        {"hostname": f"www.{domain}", "ip":"93.184.216.34", "asn":"AS15133", "country":"BR", "url": f"http://www.{domain}"},
        {"hostname": f"api.{domain}", "ip":"93.184.216.35", "asn":"AS15133", "country":"BR", "url": f"https://api.{domain}"}
    ]
