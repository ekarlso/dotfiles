from datetime import datetime, timedelta
import os
import sys
from pprint import pformat
from random import choice
import transaction

from .models import User, UserPermission, Group, SecurityGroup, GroupPermission, Resource
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

        group = SecurityGroup(
            group_name="System Admins",
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

        retailer_1 = Retailer(
            group_name="RentOurWrecks Inc",
            organization_id=3232,
            customers=[customer]).save()

        user = User(user_name="r1_booker", status=1, groups=[retailer_1],
                    email="r1_booker@random.com")
        user.set_password("r1_booker")
        user.save()

        user = User(user_name="r1_admin", status=1, groups=[retailer_1],
                    email="r1_admin@random.com")
        user.set_password("r1_admin")
        user.save()

        loc_bryne = Location(
            address="Road 1",
            city="Stavanger", postal_code=4000, retailer=retailer_1)
        loc_stavanger = Location(
            address="RoadStavanger 1",
            city="Stavanger", postal_code=4035, retailer=retailer_1)

        sub_cars = category_dict(
            ["Sedan", "Stationwagon", "SUV", "Coupe", "Pickup", "7 seats",
                "9 seats"],
            retailer_1.id)
        top_cars = Category(
            resource_name="Cars",
            owner_group_id=retailer_1.id,
            children=sub_cars.values()).save()
        sub_transport = category_dict(["Caddy", "6m 3", "11 m3", "18 m3"], retailer_1.id)
        top_transport = Category(
            resource_name="Transport",
            owner_group_id=retailer_1.id,
            children=sub_transport.values()).save()

        focus_1 = Car(retailer=retailer_1, categories=[sub_cars["Sedan"]])
        focus_1.name = "Ford: Focus - 2012 - DF00005"
        focus_1.color = "black"

        focus_2 = Car(retailer=retailer_1, categories=[sub_cars["Sedan"]]).save()
        focus_2.name = "Ford: Focus - 2012 - DF00006"
        focus_2.color = "black"

        s60_1 = Car(retailer=retailer_1, categories=[sub_cars["Sedan"]]).save()
        s60_1.name = "Volvo: S60 - 2011 - DL00007"
        s60_1.color = "black"

        s60_2 = Car(retailer=retailer_1, categories=[sub_cars["Sedan"]]).save()
        s60_2.name = "Volvo: S60 - 2011 - DL00008"
        s60_2.color = "black"

        v60_1 = Car(
            retailer=retailer_1,
            categories=[sub_cars["Stationwagon"]]).save()
        v60_1.name = "Volvo: V60 - 2012 - DL00003"
        v60_1.color = "black"

        v60_2 = Car(retailer=retailer_1, categories=[sub_cars["Stationwagon"]])
        v60_2.name = "Volvo: V60 - 2012 - DL00004"
        v60_2.color = "black"

        outlander_1 = Car(retailer=retailer_1, categories=[sub_cars["SUV"]])
        outlander_1.name = "Mitsubishi: Outlander - 2011 - DL00001"
        outlander_1.color = "black"

        outlander_2 = Car(retailer=retailer_1, categories=[sub_cars["SUV"]])
        outlander_2.name = "Mitsubishi: Outlander - 2011 - DL00002"
        outlander_2.color = "black"
        outlander_2.save()


        Booking(price=5, customer=customer, entities=[focus_1],
            created_at=(datetime.now() - timedelta(5)),
            start_location=loc_stavanger, end_location=loc_bryne)
        Booking(price=5, customer=customer, entities=[focus_2],
            start_location=loc_bryne, end_location=loc_stavanger)

        Booking(price=5, customer=customer, entities=[s60_1],
            created_at=(datetime.now() - timedelta(2)),
            start_location=loc_bryne, end_location=loc_stavanger)
        Booking(price=5, customer=customer, entities=[s60_2],
            start_location=loc_stavanger, end_location=loc_bryne)
        Booking(price=5, customer=customer, entities=[outlander_1],
            start_location=loc_stavanger, end_location=loc_bryne)
        Booking(price=5, customer=customer, entities=[outlander_2],
            start_location=loc_stavanger, end_location=loc_bryne)

        # NOTE: Rents out Trucks and Bus
        customer = Customer(name="WreckLovers Inc", organization_id=2343,
                contact="Endre Karlson", email="endre.karlson@gmail.com",
                phone="+47 xxxxxxxx").save()

        retailer_2 = Retailer(
            group_name='TransportVehicles Inc',
            organization_id=3232,
            customers=[customer]).save()

        user = User(user_name="r2_admin", status=1, groups=[retailer_2],
                    email="r2_admin@random.com").save()
        user.set_password("r2_admin")
        user.save()

        user = User(user_name="r2_booker", status=1, groups=[retailer_2],
                    email="r2_booker@random.com").save()
        user.set_password("r2_booker")
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
            retailer=retailer_2,
            categories=[sub_truck["18 m3"]]).save()
        entity_1.name = "Brand-A: Model-A - 2011 - ID-A"
        entity_1.color = "red"
        entity_2 = Car(
            retailer=retailer_2,
            categories=[sub_bus["9 seats"]]).save()
        entity_2.name = "Brand-B: Model-B - 2012 - ID-B"
        entity_2.color = "yellow"

        Booking(price=5, customer=customer, entities=[entity_1],
            created_at=(datetime.now() - timedelta(5)),
            start_location=loc_stavanger, end_location=loc_bryne)
        Booking(price=5, customer=customer, entities=[entity_1],
            start_location=loc_bryne, end_location=loc_stavanger)

        Booking(price=5, customer=customer, entities=[entity_2],
            created_at=(datetime.now() - timedelta(2)),
            start_location=loc_bryne, end_location=loc_stavanger)
        Booking(price=5, customer=customer, entities=[entity_2],
            start_location=loc_stavanger, end_location=loc_bryne)


        user = User(user_name="booker", status=1, groups=[retailer_1, retailer_2],
                    email="booker@random.com")
        user.set_password("booker")
        user.save()
