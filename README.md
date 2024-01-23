# LabCourse: Solar System Simulation - Data Generation

This repository contains a Python3 script to generate simulation data for the lab course **Solar System Simulation** according to
https://github.com/SCTeaching-NBody/LabCourse_Slides usable with https://github.com/SCTeaching-NBody/LabCourse_Implementation.

## Dependencies

Required Python3 packages:

- [tabulate](https://pypi.org/project/tabulate/)
- [astroquery](https://pypi.org/project/astroquery/)
- [requests](https://pypi.org/project/requests/)
- [argparse](https://pypi.org/project/argparse/)

They can be installed using:

```shell
pip3 install -r requirements.txt
```

## Usage

The script can be used to generate 4 different scenarios:

- **planets_and_moons**: all planets, dwarf planets, and named moons for which we could found mass specifications (177 bodies as of 2024-01-24).
- **scenario1**: all planets, dwarf planets, and named moons as well as all asteroids with a defined diameter and albedo, where the Main-belt Asteroids are additional constrained to have a diameter of at least 10km (19048 bodies as of 2024-01-24).
- **scenario2**: all planets, dwarf planets, and named moons as well as all as many asteroids such that the number of bodies is `LIMIT - 1` (minus one to account for the Sun that isn't added by this script).
- **full**: all planets, dwarf planets, named moons, and asteroids queryable through NASA's databases (1345036 bodies as of 2024-01-24).

```shell
python3 query_data.py --help
usage: query_data [-h] -o OUTPUT [-s {planets_and_moons,scenario1,scenario2,full}] [-l LIMIT]

Query asteroid data from NASA's Small Body Database.

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        the output filename containing the Keplerian Orbital Elements in CSV format
  -s {planets_and_moons,scenario1,scenario2,full}, --scenario {planets_and_moons,scenario1,scenario2,full}
                        the scenario used to create the output file
  -l LIMIT, --limit LIMIT
                        the upper limit of number of bodies for scenario2
```

The resulting csv file contains 14 columns: 

```
e,a,i,om,w,ma,epoch,H,albedo,diameter,class,name,mass,central_body
```


- the six Keplerian orbital elements (**required**): the eccentricity `e`, the semi-major axis `a` (in AU), the inclination `i` (in rad), the longitude of the ascending node `om` (in rad), the argument of periapsis `w` (in rad), and the mean anomaly `ma` (in rad)
- the `epoch` (in JD) for which the Keplerian orbital elements are valid (**required**)
- physical quantities that can be used to approximate the body's mass (**required**, but may be `0.0`!): the absolute magnitude `H`, the geometric `albedo`, and the `diameter` (in km)
- the `mass` (in kg) of the body (**optional**; if not given, approximated)
- the orbital `class` of the body (**required**; **note** that four custom (unofficial) classes where added for a better visualization)
- the [IAU name](https://www.iau.org/public/themes/naming/) of the body (**required**; may be empty)
- the `central_body` that the body orbits (**optional**; if not given, assumed to be the Sun/Sol)

**Note:** this script **never** adds the Sun/Sol to the data set since it isn't possible to represent its position using Keplerian orbital elements.
