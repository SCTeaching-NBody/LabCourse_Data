#!/usr/bin/env python3
# -*- coding: utf-8 -*-

########################################################################################################################
# Authors: Marcel Breyer, Alexander Van Craen                                                                          #
# Copyright (C): 2024 Alexander Van Craen, Marcel Breyer, and Dirk Pflüger                                             #
# License: This file is released under the MIT license. See the LICENSE file in the project root for full information. #
########################################################################################################################

import requests
import json
import csv
import argparse
import os
import urllib.parse
import string
import time
import tabulate
from dataclasses import dataclass
from astroquery.jplhorizons import Horizons

# parse command line arguments
parser = argparse.ArgumentParser(prog="query_data", description="Query planets and moons data from NASA JPL's Horizon "
                                                                "Database and asteroid data from NASA JPL's "
                                                                "Small-Body Database.")

parser.add_argument("-o", "--output",
                    help="the output filename containing the Keplerian Orbital Elements in CSV format",
                    required=True)
parser.add_argument("-s", "--scenario",
                    help="the scenario used to create the output file",
                    choices=["planets_and_moons", "scenario1", "scenario2", "full"],
                    default="full")
parser.add_argument("-l", "--limit",
                    help="the upper limit of number of bodies for scenario2",
                    type=int)

args = parser.parse_args()

# sanity check command line parameters
if args.scenario != "scenario2" and args.limit is not None:
    raise ValueError("-l/--limit may only be used with -s/--scenario scenario2")
if args.scenario == "scenario2" and args.limit is None:
    raise ValueError("-l/--limit must be provided for -s/--scenario scenario2")

print("Generating \"{}\" file for the \"{}\" scenario.".format(args.output, args.scenario))

with open(args.output, 'w+', newline='', encoding='utf-8') as csvfile:
    # write CSV file header
    writer = csv.writer(csvfile, lineterminator=os.linesep)
    writer.writerow(
        ["e", "a", "i", "om", "w", "ma", "epoch", "H", "albedo", "diameter", "class", "name", "mass", "central_body"])

    ####################################################################################################################
    #                                                                                                                  #
    #                                  retrieve planets, dwarf planets, and moons data                                 #
    #                                                                                                                  #
    ####################################################################################################################

    # query major bodies data from JPL Horizons database using astroquery. For more information see:
    # https://astroquery.readthedocs.io/en/latest/jplhorizons/jplhorizons.html
    # https://ssd-api.jpl.nasa.gov/doc/horizons.html
    # https://science.nasa.gov/solar-system/moons/

    # since Horizons doesn't return masses, we have to explicitly list all planets and named moons where we know a mass

    @dataclass
    class Body:
        name: str
        orbit_class: str
        central_body: str
        mass: float


    # list of all planets and moons with the associated mass
    major_bodies_dict = {
        # planets
        199: Body("Mercury", "PLA", "Sun", 3.301011e+23),
        299: Body("Venus", "PLA", "Sun", 4.867320e+24),
        399: Body("Earth", "PLA", "Sun", 5.972186e+24),
        499: Body("Mars", "PLA", "Sun", 6.416928e+23),
        599: Body("Jupiter", "PLA", "Sun", 1.898130e+27),
        699: Body("Saturn", "PLA", "Sun", 5.683191e+26),
        799: Body("Uranus", "PLA", "Sun", 8.681013e+25),
        899: Body("Neptune", "PLA", "Sun", 1.024096e+26),

        # dwarf planets
        "Ceres": Body("Ceres", "DWA", "Sun", 9.47e+20),
        999: Body("Pluto", "DWA", "Sun", 1.302933e+22),
        136199: Body("Eris", "DWA", "Sun", 1.671600e+22),
        136108: Body("Haumea", "DWA", "Sun", 4.006000e+21),
        136472: Body("Makemake", "DWA", "Sun", 3.100000e+21),
        225088: Body("Gonggong", "DWA", "Sun", 1.750000e+21),
        50000: Body("Quaoar", "DWA", "Sun", 1.400000e+21),
        90377: Body("Sedna", "DWA", "Sun", 1.194000e+21),
        90482: Body("Orcus", "DWA", "Sun", 6.348000e+20),
        120347: Body("Salacia", "DWA", "Sun", 4.922000e+20),

        # Earth moon
        301: Body("Luna", "SAT", "Earth", 7.345811e+22),

        # Mars moons
        401: Body("Phobos", "SAT", "Mars", 1.061919e+16),
        402: Body("Deimos", "SAT", "Mars", 1.440690e+15),

        # Jupiter moons
        501: Body("Io", "SAT", "Jupiter", 8.929676e+22),
        502: Body("Europa", "SAT", "Jupiter", 4.798588e+22),
        503: Body("Ganymede", "SAT", "Jupiter", 1.481483e+23),
        504: Body("Callisto", "SAT", "Jupiter", 1.075664e+23),
        505: Body("Amalthea", "SAT", "Jupiter", 2.465636e+18),
        506: Body("Himalia", "SAT", "Jupiter", 2.270693e+18),
        507: Body("Elara", "SAT", "Jupiter", 8.692277e+17),
        508: Body("Pasiphae", "SAT", "Jupiter", 2.997337e+17),
        509: Body("Sinope", "SAT", "Jupiter", 7.493342e+16),
        510: Body("Lysithea", "SAT", "Jupiter", 6.294407e+16),
        511: Body("Carme", "SAT", "Jupiter", 1.318828e+17),
        512: Body("Ananke", "SAT", "Jupiter", 2.997337e+16),
        513: Body("Leda", "SAT", "Jupiter", 1.094028e+16),
        514: Body("Thebe", "SAT", "Jupiter", 4.517042e+17),
        515: Body("Adrastea", "SAT", "Jupiter", 2.082622e+15),
        516: Body("Metis", "SAT", "Jupiter", 3.747221e+16),
        517: Body("Callirrhoe", "SAT", "Jupiter", 8.692277e+14),
        518: Body("Themisto", "SAT", "Jupiter", 6.893875e+14),
        519: Body("Megaclite", "SAT", "Jupiter", 2.098136e+14),
        520: Body("Taygete", "SAT", "Jupiter", 1.648535e+14),
        521: Body("Chaldene", "SAT", "Jupiter", 7.493342e+13),
        522: Body("Harpalyke", "SAT", "Jupiter", 1.198935e+14),
        523: Body("Kalyke", "SAT", "Jupiter", 1.948269e+14),
        524: Body("Iocaste", "SAT", "Jupiter", 1.948269e+14),
        525: Body("Erinome", "SAT", "Jupiter", 4.496005e+13),
        526: Body("Isonoe", "SAT", "Jupiter", 7.493342e+13),
        527: Body("Praxidike", "SAT", "Jupiter", 4.346138e+14),
        528: Body("Autonoe", "SAT", "Jupiter", 8.992011e+13),
        529: Body("Thyone", "SAT", "Jupiter", 8.992011e+13),
        530: Body("Hermippe", "SAT", "Jupiter", 8.992011e+13),
        531: Body("Aitne", "SAT", "Jupiter", 4.496005e+13),
        532: Body("Eurydome", "SAT", "Jupiter", 4.496005e+13),
        533: Body("Euanthe", "SAT", "Jupiter", 4.496005e+13),
        534: Body("Euporie", "SAT", "Jupiter", 1.498668e+13),
        535: Body("Orthosie", "SAT", "Jupiter", 1.498668e+13),
        536: Body("Sponde", "SAT", "Jupiter", 1.498668e+13),
        537: Body("Kale", "SAT", "Jupiter", 1.498668e+13),
        538: Body("Pasithee", "SAT", "Jupiter", 1.498668e+13),
        539: Body("Hegemone", "SAT", "Jupiter", 4.496005e+13),
        540: Body("Mneme", "SAT", "Jupiter", 1.498668e+13),
        541: Body("Aoede", "SAT", "Jupiter", 8.992011e+13),
        542: Body("Thelxinoe", "SAT", "Jupiter", 1.498668e+13),
        543: Body("Arche", "SAT", "Jupiter", 4.496005e+13),
        544: Body("Kallichore", "SAT", "Jupiter", 1.498668e+13),
        545: Body("Helike", "SAT", "Jupiter", 8.992011e+13),
        546: Body("Carpo", "SAT", "Jupiter", 4.496005e+13),
        547: Body("Eukelade", "SAT", "Jupiter", 8.992011e+13),
        548: Body("Cyllene", "SAT", "Jupiter", 1.498668e+13),
        549: Body("Kore", "SAT", "Jupiter", 1.498668e+13),
        550: Body("Herse", "SAT", "Jupiter", 1.498668e+13),
        553: Body("Dia", "SAT", "Jupiter", 5.520000e+12),
        557: Body("Eirene", "SAT", "Jupiter", 5.520000e+12),
        558: Body("Philophrosyne", "SAT", "Jupiter", 2.760000e+12),
        560: Body("Eupheme", "SAT", "Jupiter", 2.760000e+12),
        562: Body("Valetudo", "SAT", "Jupiter", 1.380000e+12),
        565: Body("Pandia", "SAT", "Jupiter", 4.140000e+12),
        571: Body("Ersa", "SAT", "Jupiter", 4.140000e+12),

        # Saturn moons
        601: Body("Mimas", "SAT", "Saturn", 3.750950e+19),
        602: Body("Enceladus", "SAT", "Saturn", 1.080321e+20),
        603: Body("Tethys", "SAT", "Saturn", 6.174978e+20),
        604: Body("Dione", "SAT", "Saturn", 1.095490e+21),
        605: Body("Rhea", "SAT", "Saturn", 2.306492e+21),
        606: Body("Titan", "SAT", "Saturn", 1.345184e+23),
        607: Body("Hyperion", "SAT", "Saturn", 5.551031e+18),
        608: Body("Iapetus", "SAT", "Saturn", 1.805665e+21),
        609: Body("Phoebe", "SAT", "Saturn", 8.312297e+18),
        610: Body("Janus", "SAT", "Saturn", 1.896482e+18),
        611: Body("Epimetheus", "SAT", "Saturn", 5.262490e+17),
        612: Body("Helene", "SAT", "Saturn", 7.127989e+15),
        613: Body("Telesto", "SAT", "Saturn", 4.046405e+15),
        614: Body("Calypso", "SAT", "Saturn", 2.547736e+15),
        615: Body("Atlas", "SAT", "Saturn", 5.571944e+15),
        616: Body("Prometheus", "SAT", "Saturn", 1.610972e+17),
        617: Body("Pandora", "SAT", "Saturn", 1.391959e+17),
        618: Body("Pan", "SAT", "Saturn", 4.945606e+15),
        619: Body("Ymir", "SAT", "Saturn", 4.945606e+15),
        620: Body("Paaliaq", "SAT", "Saturn", 8.242676e+15),
        621: Body("Tarvos", "SAT", "Saturn", 2.697603e+15),
        622: Body("Ijiraq", "SAT", "Saturn", 1.198935e+15),
        623: Body("Suttungr", "SAT", "Saturn", 2.098136e+14),
        624: Body("Kiviuq", "SAT", "Saturn", 3.297071e+15),
        625: Body("Mundilfari", "SAT", "Saturn", 2.098136e+14),
        626: Body("Albiorix", "SAT", "Saturn", 2.098136e+16),
        627: Body("Skathi", "SAT", "Saturn", 3.147204e+14),
        628: Body("Erriapus", "SAT", "Saturn", 7.643209e+14),
        629: Body("Siarnaq", "SAT", "Saturn", 3.896538e+16),
        630: Body("Thrymr", "SAT", "Saturn", 2.098136e+14),
        631: Body("Narvi", "SAT", "Saturn", 3.446937e+14),
        632: Body("Methone", "SAT", "Saturn", 8.992011e+12),
        633: Body("Pallene", "SAT", "Saturn", 3.297071e+13),
        634: Body("Polydeuces", "SAT", "Saturn", 4.496005e+12),
        635: Body("Daphnis", "SAT", "Saturn", 7.793076e+13),
        636: Body("Aegir", "SAT", "Saturn", 2.599000e+14),
        637: Body("Bebhionn", "SAT", "Saturn", 2.599000e+14),
        638: Body("Bergelmir", "SAT", "Saturn", 2.599000e+14),
        639: Body("Bestla", "SAT", "Saturn", 4.140000e+14),
        640: Body("Farbauti", "SAT", "Saturn", 1.495000e+14),
        641: Body("Fenrir", "SAT", "Saturn", 7.820000e+13),
        642: Body("Fornjot", "SAT", "Saturn", 8.280000e+12),
        643: Body("Hati", "SAT", "Saturn", 2.599000e+14),
        644: Body("Hyrrokkin", "SAT", "Saturn", 2.599000e+14),
        645: Body("Kari", "SAT", "Saturn", 2.599000e+14),
        646: Body("Loge", "SAT", "Saturn", 2.599000e+14),
        647: Body("Skoll", "SAT", "Saturn", 2.599000e+14),
        648: Body("Surtur", "SAT", "Saturn", 2.599000e+14),
        649: Body("Anthe", "SAT", "Saturn", 1.498668e+12),
        650: Body("Jarnsaxa", "SAT", "Saturn", 2.599000e+14),
        651: Body("Greip", "SAT", "Saturn", 2.599000e+14),
        652: Body("Tarqeq", "SAT", "Saturn", 2.599000e+14),
        653: Body("Aegaeon", "SAT", "Saturn", 5.994674e+10),

        # Uranus moons
        701: Body("Ariel", "SAT", "Uranus", 1.250524e+21),
        702: Body("Umbriel", "SAT", "Uranus", 1.274945e+21),
        703: Body("Titania", "SAT", "Uranus", 3.400272e+21),
        704: Body("Oberon", "SAT", "Uranus", 3.076338e+21),
        705: Body("Miranda", "SAT", "Uranus", 6.471884e+19),
        706: Body("Cordelia", "SAT", "Uranus", 4.496005e+16),
        707: Body("Ophelia", "SAT", "Uranus", 5.395206e+16),
        708: Body("Bianca", "SAT", "Uranus", 9.291744e+16),
        709: Body("Cressida", "SAT", "Uranus", 3.431951e+17),
        710: Body("Desdemona", "SAT", "Uranus", 1.783415e+17),
        711: Body("Juliet", "SAT", "Uranus", 5.575047e+17),
        712: Body("Portia", "SAT", "Uranus", 1.681506e+18),
        713: Body("Rosalind", "SAT", "Uranus", 2.547736e+17),
        714: Body("Belinda", "SAT", "Uranus", 3.566831e+17),
        715: Body("Puck", "SAT", "Uranus", 2.893929e+18),
        716: Body("Caliban", "SAT", "Uranus", 2.997337e+17),
        717: Body("Sycorax", "SAT", "Uranus", 2.697603e+18),
        718: Body("Prospero", "SAT", "Uranus", 9.891212e+16),
        719: Body("Setebos", "SAT", "Uranus", 8.692277e+16),
        720: Body("Stephano", "SAT", "Uranus", 2.547736e+16),
        721: Body("Trinculo", "SAT", "Uranus", 4.645872e+15),
        722: Body("Francisco", "SAT", "Uranus", 8.392543e+15),
        723: Body("Margaret", "SAT", "Uranus", 6.294407e+15),
        724: Body("Ferdinand", "SAT", "Uranus", 6.294407e+15),
        725: Body("Perdita", "SAT", "Uranus", 1.800000e+16),
        726: Body("Mab", "SAT", "Uranus", 1.000000e+15),
        727: Body("Cupid", "SAT", "Uranus", 3.800000e+15),

        # Neptune moons
        801: Body("Triton", "SAT", "Neptune", 2.140299e+22),
        802: Body("Nereid", "SAT", "Neptune", 3.087257e+19),
        803: Body("Naiad", "SAT", "Neptune", 1.278083e+17),
        804: Body("Thalassa", "SAT", "Neptune", 3.534274e+17),
        805: Body("Despina", "SAT", "Neptune", 1.748980e+18),
        806: Body("Galatea", "SAT", "Neptune", 2.845228e+18),
        807: Body("Larissa", "SAT", "Neptune", 3.818296e+18),
        808: Body("Proteus", "SAT", "Neptune", 3.870713e+19),
        809: Body("Halimede", "SAT", "Neptune", 8.992011e+16),
        810: Body("Psamathe", "SAT", "Neptune", 1.498668e+16),
        811: Body("Sao", "SAT", "Neptune", 8.992011e+16),
        812: Body("Laomedeia", "SAT", "Neptune", 8.992011e+16),
        813: Body("Neso", "SAT", "Neptune", 1.648535e+17),
        814: Body("Hippocamp", "SAT", "Neptune", 1.500000e+16),

        # Pluto moons
        901: Body("Charon", "SAT", "Pluto", 1.586388e+21),
        902: Body("Nix", "SAT", "Pluto", 4.567048e+16),
        903: Body("Hydra", "SAT", "Pluto", 4.811065e+16),
        904: Body("Kerberos", "SAT", "Pluto", 1.663162e+16),
        905: Body("Styx", "SAT", "Pluto", 7.500000e+15),
    }

    start_time = time.time()

    # query JPL Horizons database
    jpl_horizons_data = []
    for body in major_bodies_dict:
        location_query = ""
        if major_bodies_dict[body].central_body == "Sun":
            location_query = "@sun"
        elif major_bodies_dict[body].central_body == "Earth":
            location_query = "Geocentric"
        else:
            location_query = "{} Barycenter".format(major_bodies_dict[body].central_body)
        obj = Horizons(id=body, location=location_query, epochs=2451544.5)
        eph = obj.elements()

        eph["a"].convert_unit_to('au')
        jpl_horizons_data.append([eph["e"][0], eph["a"][0], eph["incl"][0], eph["Omega"][0], eph["w"][0], eph["M"][0],
                                  eph["datetime_jd"][0], '', '', '', major_bodies_dict[body].orbit_class,
                                  major_bodies_dict[body].name, major_bodies_dict[body].mass,
                                  major_bodies_dict[body].central_body])

    # write bundled data to file
    writer.writerows(jpl_horizons_data)

    end_time = time.time()
    print("NASA Horizons Database: {:.2f}s".format(end_time - start_time))

    if args.limit is not None:
        if args.limit < len(jpl_horizons_data) + 1:
            raise ValueError("-l/--limit ({}) must be at least as large as the number of planets and moons + 1 ("
                             "accounting for the Sun) which is {}!".format(args.limit, len(jpl_horizons_data) + 1))
        # when querying the number of asteroid with an upper limit,
        # also take the already added planets and moons in to account
        args.limit -= len(jpl_horizons_data) + 1

    ####################################################################################################################
    #                                                                                                                  #
    #                                              retrieve asteroid data                                              #
    #                                                                                                                  #
    ####################################################################################################################

    if args.scenario != "planets_and_moons":
        # query asteroid data using NASA JPL's Small Body Database. For more information see:
        # https://ssd-api.jpl.nasa.gov/doc/sbdb_query.html
        # https://ssd-api.jpl.nasa.gov/doc/sbdb_filter.html

        # the NASA JPL Small Body Database Query API URL
        url = "https://ssd-api.jpl.nasa.gov/sbdb_query.api"
        # all necessary fields + the total number of bodies return from the API
        fields = "full-prec=true&fields=e,a,i,om,w,ma,epoch,H,albedo,diameter,class,full_name"

        # each line adds two empty CSV entry in the end:
        # tha mass of asteroids isn't known
        # the central body of all asteroids is, by definition, the Sun
        writer = csv.writer(csvfile, lineterminator=",,{}".format(os.linesep))

        # request the asteroid from NASA JPL's Small Body Database
        constraint = ""
        if args.scenario == "scenario1":
            # scenario1: all asteroids with a given diameter and albedo where all main-belt asteroids are
            #            additionally constrained to have a diameter equal or larger than 10km
            query = r'''
            {
                "AND": [
                    { "AND" : [ "diameter|DF", "albedo|DF" ] },
                    { "OR" : [ "class|NE|MBA", "diameter|GE|10" ] }
                ]
            }
            '''
            # minify json string by removing all whitespace characters
            query = query.translate({ord(c): None for c in string.whitespace})
            # convert string to URI representation
            constraint = "&sb-cdata={}".format(urllib.parse.quote(query))
        elif args.scenario == "scenario2":
            constraint = "&limit={}".format(args.limit)

        start_time = time.time()

        # request data
        req = requests.get("{}?{}{}&sb-kind=a".format(url, fields, constraint))
        # check whether the query was successful
        if req.status_code != 200:
            raise RuntimeError("Error {} performing request. For more information see "
                               "https://ssd-api.jpl.nasa.gov/doc/sbdb_query.html#http-response-codes.".format(
                                req.status_code))

        # the response is a JSON string -> convert it to a JSON object
        jpl_sb_data = json.loads(req.text)
        # write all queried bodies to the CSV file
        writer.writerows(jpl_sb_data["data"])

        end_time = time.time()
        print("NASA JPL Small Body Database: {:.2f}s".format(end_time - start_time))

    ####################################################################################################################
    #                                                                                                                  #
    #                                               calculate statistics                                               #
    #                                                                                                                  #
    ####################################################################################################################

    orbit_classes = {
        # custom orbit classes
        "PLA": ["Planets", 0],
        "DWA": ["Dwarf Planets", 0],
        "SAT": ["Moons", 0],
        # official asteroid orbit classes
        "IEO": ["Atira", 0],
        "ATE": ["Aten", 0],
        "APO": ["Apollo", 0],
        "AMO": ["Amor", 0],
        "MCA": ["Mars-crossing Asteroid", 0],
        "IMB": ["Inner Main-belt Asteroid", 0],
        "MBA": ["Main-belt Asteroid", 0],
        "OMB": ["Outer Main-belt Asteroid", 0],
        "TJN": ["Jupiter Trojan", 0],
        "AST": ["Asteroid", 0],
        "CEN": ["Centaur", 0],
        "TNO": ["TransNeptunian Object", 0],
        "PAA": ["Parabolic \"Asteroid\"", 0],
        "HYA": ["Hyperbolic \"Asteroid\"", 0]
    }
    for mbo in jpl_horizons_data:
        orbit_classes[mbo[10]][1] += 1
    if args.scenario != "planets_and_moons":
        for sbo in jpl_sb_data["data"]:
            orbit_classes[sbo[10]][1] += 1

    # output the number of bodies per orbit class
    table = [["{} ({})".format(oc, orbit_classes[oc][0]), orbit_classes[oc][1]] for oc in orbit_classes]
    # print table
    print()
    print(tabulate.tabulate(table, headers=["orbit class", "occurrences"], tablefmt="github"))
    print()

    # print the total number of requested bodies
    total_number_of_bodies = 0
    for oc in orbit_classes:
        total_number_of_bodies += orbit_classes[oc][1]
    print("Total number of bodies is {} + 1 (Sun) = {}.".format(total_number_of_bodies, total_number_of_bodies + 1))
