from fastmcp import FastMCP

mcp = FastMCP(name="weather-server")

@mcp.tool()
def get_weather(city: str) -> str:
    data = {
        "chennai": "32°C, humid",
        "delhi": "18°C, foggy",
        "bangalore": "24°C, pleasant"
    }
    return data.get(city.lower(), "Weather not available")

if __name__ == "__main__":
    #mcp.run()
    mcp.run(transport="sse")
