# U.S Energy Information Adminisration (EIA)

Retrieve data from [EIA](https://www.eia.gov/)

## Retrieve data

First [register](https://www.eia.gov/opendata/register.php) to get an
API-key. This is assumed to be in `$EIA_KEY` below.

Data is retrieved via a [REST](https://en.wikipedia.org/wiki/REST)
API, described [here](https://www.eia.gov/opendata/documentation.php).
The API can be used with a program or with [curl](https://curl.se/).
The responses are in [json](https://en.wikipedia.org/wiki/JSON) format
and can be handled with [jq](https://jqlang.org/).

Data is hierarchy:

> Datasets that are arranged in a logical hierarchy. Member datasets may
> be discovered by querying their parent node.

This mean that we can examine what data that is available by querying
meta data (data about data) for each node.

```
curl -gL https://api.eia.gov/v2/?api_key=$EIA_KEY > top
# for some reson jq doesn't like '\/' in values
cat top | sed -e 's,\\/,/,' | jq
cat top | sed -e 's,\\/,/,' | jq -r '.response.routes[].id'
coal
crude-oil-imports
electricity
international
natural-gas
nuclear-outages
petroleum
seds
steo
densified-biomass
total-energy
aeo
ieo
co2-emissions
```

The path to a node is called `route`. The example above shows all
routes from the top node. We will focus on "international". There is
also an [interactive page](https://www.eia.gov/international/data/world)
for this.

Let's dive one level deeper:
```
curl -gL https://api.eia.gov/v2/international/?api_key=$EIA_KEY > international
cat international | sed -e 's,\\/,/,' | jq -r '.response.facets[].id'
productId
activityId
countryRegionId
countryRegionTypeId
dataFlagId
unit
```

In this node we have no routes, but there are `facets`. They are used
to select or filter received data. To download a complete dataset
(which may be *huge*) is unnecessary (always) so facets should
*always* be used to limit the output. There is a limit on 5000 rows of
data in one chunk, so we really want to be below that.

Next step is to examine what values that can be set for a facet.
```
curl -gL https://api.eia.gov/v2/international/facet/countryRegionId?api_key=$EIA_KEY > countryRegionId
cat countryRegionId | sed -e 's,\\/,/,' | jq -r '.response.facets[]'
# offf, that was a lot! But let's focus on
{
  "id": "WORL",
  "name": "World"
}
```
With this we can limit our data to "World", and avoid downloding data
for *all* regions. Still there is a lot that we *don't* want.

```
curl -gL https://api.eia.gov/v2/international/facet/activityId?api_key=$EIA_KEY > activityId
cat activityId | sed -e 's,\\/,/,' | jq -r '.response.facets[]'
{
  "id": "2",
  "name": "Consumption"
}
```

Now we are ready to check the actual data to check the number of rows.
In this example we only want the total world energy consumption
(Primary energy) in MTOE.

```
curl -gL "https://api.eia.gov/v2/international/data/?frequency=annual&data[0]=value&facets[countryRegionId][]=WORL&facets[activityId][]=2&facets[unit][]=MTOE&api_key=$EIA_KEY" > resp
cat resp | sed -e 's,\\/,/,' | jq
```

Still too much. We want "Primary energy" only. We can see in the data
that this has `productId=44`, which doesn't show if we check the
"productId" facet as described above, but never mind, now we know.
The final qeries:

```
curl -gL "https://api.eia.gov/v2/international/data/?frequency=annual&data[0]=value&facets[countryRegionId][]=WORL&facets[activityId][]=2&facets[unit][]=MTOE&facets[productId][]=44&start=1966-01-01&end=2025-01-01&api_key=$EIA_KEY" > energyConsumption
curl -gL "https://api.eia.gov/v2/international/data/?frequency=annual&data[0]=value&facets[countryRegionId][]=WORL&facets[activityId][]=1&facets[unit][]=MTOE&facets[productId][]=44&start=1966-01-01&end=2025-01-01&api_key=$EIA_KEY" > energyProduction
cat data/energyProduction | sed -e 's,\\/,/,' | jq
cat data/energyConsumption | sed -e 's,\\/,/,' | jq
```

[Wikipedia](https://en.wikipedia.org/wiki/World_energy_supply_and_consumption)
says that the total energy production 2021 was 14,800 MToe. Our data
says 14,400 MToe, so it't close but not exactly the same.

[Our World in Data](https://ourworldindata.org/energy-production-consumption)
says that for 2021 the *consumption* is 175,926 TWh, which is ~15,126
MToe. Our consumption data says 14,236 MToe, but they claim to use
data "with major processing by Our World in Data". Most notable the
"substitution method" which increase the values for renewable sources.

Lesson to learn: *compare data from the same source*!

