import requests
import os
from discord.ext import commands
import discord
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def geocode_city(city, state=None, country=None):
    """Resolve a city name (including Japanese) to lat/lon via the Geocoding API."""
    parts = [p for p in [city, state, country] if p]
    query = ",".join(parts)
    r = requests.get(
        "http://api.openweathermap.org/geo/1.0/direct",
        params={"q": query, "limit": 1, "appid": OPENWEATHER_API_KEY}
    )
    data = r.json()
    return data[0] if data else None


def get_weather_by_coords(lat, lon):
    """Fetch weather data using coordinates."""
    r = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"lat": lat, "lon": lon, "units": "metric", "appid": OPENWEATHER_API_KEY}
    )
    return r.json()


def format_location(geo: dict) -> str:
    """Build a display name from geocoding result, preferring local name."""
    local_names = geo.get("local_names", {})
    name = local_names.get("ja") or geo.get("name", "")
    state = geo.get("state", "")
    country = geo.get("country", "")
    parts = [p for p in [name, state, country] if p]
    return ", ".join(parts)


@commands.group(
    help="Displays weather in requested city",
    description="Command: !weather <city> <state> <country>",
    brief="Displays weather in requested city"

)

async def weather (ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send(f"No, {ctx.subcommand_passed} does not belong to the weather command")


#current weather command with city, state and country inputs
@weather.command()
@commands.cooldown(2, 1, commands.BucketType.default)
async def currentweather(ctx, city: str, state: str = None, country: str = None):
    geo = geocode_city(city, state, country)
    if not geo:
        await ctx.send("Could not find that city. Please try again.")
        return

    json_data = get_weather_by_coords(geo["lat"], geo["lon"])

    weather_main = json_data['weather'][0]['main']
    description = json_data['weather'][0]['description']
    temp = json_data['main']['temp']
    icon = "http://openweathermap.org/img/wn/" + json_data['weather'][0]['icon'] + "@2x.png"

    embed = discord.Embed(
        title="Current Weather",
        description=format_location(geo),
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name=weather_main, value=description, inline=False)
    embed.add_field(name="Temperature", value=f"{temp}\u2103", inline=False)

    await ctx.send(embed=embed)

#creating error handler for city and country
@currentweather.error
async def currentweather_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown, please wait a few seconds before inputting the command again")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("This is not a valid city or country, please try again.")

#current weather command with only city input

@weather.command()
@commands.cooldown(2, 1, commands.BucketType.default)
async def city(ctx, *, city: str):
    geo = geocode_city(city)
    if not geo:
        await ctx.send("Could not find that city. Please try again.")
        return

    json_data = get_weather_by_coords(geo["lat"], geo["lon"])

    weather_main = json_data['weather'][0]['main']
    description = json_data['weather'][0]['description']
    temp = json_data['main']['temp']
    icon = "http://openweathermap.org/img/wn/" + json_data['weather'][0]['icon'] + "@2x.png"

    embed = discord.Embed(
        title="Current Weather",
        description=format_location(geo),
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name=weather_main, value=description, inline=False)
    embed.add_field(name="Temperature", value=f"{temp}\u2103", inline=False)

    await ctx.send(embed=embed)

#creating error handler for city
@city.error
async def city_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("This command is on cooldown, please wait a few seconds before inputting the command again")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("This is not a valid city, please try again.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing city, please input proper city")
        
async def setup(client):
    client.add_command(weather)