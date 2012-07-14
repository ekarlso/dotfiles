from datetime import datetime, timedelta
import os
import sys
from pprint import pformat
from random import choice
import transaction

from .models import User, UserPermission, Group, GroupPermission, Resource
from .models import Retailer, Customer, Booking, Location
from .models import Category, Entity, EntityMetadata, DrivableEntity, Car


def category_dict(names, owner_group_id):
    return dict([(n, Category(resource_name=n,
                owner_group_id=owner_group_id)) for n in names])


def populate():
    pass


def populate_samples():
    populate()
    with transaction.manager:
        g_admin = GroupPermission(perm_name="admin")

        group = Group(
            group_name="System Admins",
            group_type="security",
            permissions=[g_admin]).save()

        admin = User(user_name="admin", status=1, groups=[group],
            email="endre.karlson@gmail.com",
            first_name="Endre", last_name="Karlson")
        admin.set_password("admin")
        admin.save()


        # NOTE: First Retailer rents out cars and transport class cars
        customer = Customer(name="WreckRenters Inc", organization_id=2343,
                    contact="Steffen Soma", email="stefsoma@gmail.com",
                    phone="+47 xxxxxxxx")

        retailer = Retailer(
            group_name="RentOurWrecks Inc",
            group_type="retailer",
            organization_id=3232,
            customers=[customer]).save()

        user = User(user_name="booker1", status=1, groups=[retailer],
                    email="booker1@random.com")
        user.set_password("booker1")
        user.save()

        loc_bryne = Location(
            address="Road 1",
            city="Stavanger", postal_code=4000, retailer=retailer)
        loc_stavanger = Location(
            address="RoadStavanger 1",
            city="Stavanger", postal_code=4035, retailer=retailer)

        sub_cars = category_dict(
            ["Sedan", "Stationwagon", "SUV", "Coupe", "Pickup", "7 seats",
                "9 seats"],
            retailer.id)
        top_cars = Category(
            resource_name="Cars",
            owner_group_id=retailer.id,
            children=sub_cars.values()).save()
        sub_transport = category_dict(["Caddy", "6m 3", "11 m3", "18 m3"], retailer.id)
        top_transport = Category(
            resource_name="Transport",
            owner_group_id=retailer.id,
            children=sub_transport.values()).save()

        focus_1 = Car(
            brand="Ford",
            model="Focus",
            identifier="DF00005",
            produced=2012,
            retailer=retailer,
            categories=[sub_cars["Sedan"]]).save()
        focus_2 = Car(
            brand="Ford",
            model="Focus",
            identifier="DF00006",
            produced=2012,
            retailer=retailer,
            categories=[sub_cars["Sedan"]]).save()
        s60_1 = Car(
            brand="Volvo",
            model="S60",
            identifier="DL00007",
            produced=2011,
            retailer=retailer,
            categories=[sub_cars["Sedan"]]).save()
        s60_2 = Car(
            brand="Volvo",
            model="S60",
            identifier="DL00008",
            produced=2011,
            retailer=retailer,
            categories=[sub_cars["Sedan"]]).save()
        xc60_1 = Car(
            brand="Volvo",
            model="V60",
            identifier="DL00003",
            produced=2012,
            retailer=retailer,
            categories=[sub_cars["Stationwagon"]]).save()
        xc60_2 = Car(
            brand="Volvo",
            model="V60",
            identifier="DL00004",
            produced=2012,
            retailer=retailer,
            categories=[sub_cars["Stationwagon"]]).save()
        outlander_1 = Car(
            brand="Mitsubishi",
            model="Outlander",
            identifier="DL00001",
            produced=2011,
            retailer=retailer,
            categories=[sub_cars["SUV"]]).save()
        outlander_2 = Car(
            brand="Mitsubishi",
            model="Outlander",
            identifier="DL00002",
            produced=2011,
            retailer=retailer,
            categories=[sub_cars["SUV"]]).save()


        Booking(price=5, customer=customer, entity=focus_1,
            created_at=(datetime.now() - timedelta(5)),
            start_location=loc_stavanger, end_location=loc_bryne)
        Booking(price=5, customer=customer, entity=focus_2,
            start_location=loc_bryne, end_location=loc_stavanger)

        Booking(price=5, customer=customer, entity=s60_1,
            created_at=(datetime.now() - timedelta(2)),
            start_location=loc_bryne, end_location=loc_stavanger)
        Booking(price=5, customer=customer, entity=s60_2,
            start_location=loc_stavanger, end_location=loc_bryne)
        Booking(price=5, customer=customer, entity=outlander_1,
            start_location=loc_stavanger, end_location=loc_bryne)
        Booking(price=5, customer=customer, entity=outlander_2,
            start_location=loc_stavanger, end_location=loc_bryne)

        # NOTE: Rents out Trucks and Bus
        customer = Customer(name="WreckLovers Inc", organization_id=2343,
                contact="Endre Karlson", email="endre.karlson@gmail.com",
                phone="+47 xxxxxxxx").save()

        retailer_2 = Retailer(
            group_name='TransportVehicles Inc',
            group_type="retailer",
            organization_id=3232,
            customers=[customer]).save()
        user = User(user_name="booker2", status=1, groups=[retailer],
                    email="booker2@random.com").save()
        user.set_password("booker2")
        user.save()

        user = User(user_name="steffen", status=1, groups=[retailer_2],
                    first_name="Steffen", middle_name="Tenold",
                    last_name="Soma",
                    email="steffen.soma@gmail.com").save()
        user.set_password("password")
        user.save()

        sub_truck = category_dict(
            ["18 m3", "22 m3", "26 m3", "35 m3"],
            owner_group_id=retailer_2.id)
        top_truck = Category(
            resource_name="Truck",
            children=sub_truck.values(),
            owner_group_id=retailer_2.id).save()
        sub_bus = category_dict(
            ["9 seats", "17 seats"],
            owner_group_id=retailer_2.id)
        top_bus = Category(
            resource_name="Mini bus",
            children=sub_bus.values(),
            owner_group_id=retailer_2.id).save()

        loc_bryne = Location(
            address="RoadBryne 1",
            city="Stavanger", postal_code=4000, retailer=retailer_2)
        loc_stavanger = Location(
            address="RoadStavanger 1",
            city="Stavanger", postal_code=4035, retailer=retailer_2)

        entity_1 = Car(
            brand="Brand-A",
            model="Model-A",
            identifier="ID-A",
            produced=2004,
            retailer=retailer_2,
            categories=[sub_truck["18 m3"]]).save()
        entity_2 = Car(
            brand="Brand-B",
            model="Model-B",
            identifier="ID-B",
            produced=2011,
            retailer=retailer_2,
            categories=[sub_bus["9 seats"]]).save()

        Booking(price=5, customer=customer, entity=entity_1,
            created_at=(datetime.now() - timedelta(5)),
            start_location=loc_stavanger, end_location=loc_bryne)
        Booking(price=5, customer=customer, entity=entity_1,
            start_location=loc_bryne, end_location=loc_stavanger)

        Booking(price=5, customer=customer, entity=entity_2,
            created_at=(datetime.now() - timedelta(2)),
            start_location=loc_bryne, end_location=loc_stavanger)
        Booking(price=5, customer=customer, entity=entity_2,
            start_location=loc_stavanger, end_location=loc_bryne)
