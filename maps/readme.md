
# Maps

Maps are created with either Matplotlib/Basemap or as a geojson file on an anonymous gist.

Choose which map type you'd like by using the `-l` argument:

```
  -l , --location       Map location. choices: (NA, EU, World, Geo)
                        (default: NA)
```

# Requirements

- [ ] [Matplotlib](https://matplotlib.org/1.2.1/users/installing.html)
- [ ] [Basemap](https://matplotlib.org/basemap/users/installing.html)

\* not required if creating geojson maps


## Matplotlib map examples:

<ul>
<li><details>
<summary>NA_map_example</a></summary>

![NA_map_example](https://github.com/blacktwin/JBOPS/raw/master/maps/NA_map_example.PNG "NA_map_example")

</details></li>

<li><details>
<summary>EU_map_example</a></summary>

![EU_map_example](https://github.com/blacktwin/JBOPS/raw/master/maps/EU_map_example.PNG "EU_map_example")

</details></li>

<li><details>
<summary>World_map_example</a></summary>

![World_map_example](https://github.com/blacktwin/JBOPS/raw/master/maps/World_map_example.PNG "World_map_example")
</details></li>
</ul>

## TODO LIST:

- [x] Add check for user count in user_table to allow for greater than 25 users - [Pull](https://github.com/blacktwin/JBOPS/pull/3)
- [x] If platform is missing from PLATFORM_COLORS use DEFAULT_COLOR - [Pull](https://github.com/blacktwin/JBOPS/pull/4)
- [x] Add arg to allow for runs in headless (mpl.use("Agg")) 
- [x] Add pass on N/A values for Lon/Lat - [Pull](https://github.com/blacktwin/JBOPS/pull/2)

### Feature updates:

- [ ] Add arg for legend (best, none, axes)
- [ ] Find server's external IP, geolocation. Allow custom location to override
- [ ] Add arg for tracert visualization from server to client
- [ ] Animate tracert visualization? gif?
- [ ] UI, toggles, interactive mode



