import os
import sys
import transaction
from pprint import pformat

from random import choice

from sqlalchemy import engine_from_config

from pyramid.paster import get_appsettings, setup_logging

from ..models import (
    configure_db, User, UserPermission, Group, GroupPermission, Resource,
    Customer, DrivableEntity, Category, Property
)


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)

    configure_db(settings)

    load_samples()


def category_dict(names):
    #print names
    return dict([(n, Category(name=n)) for n in names])


def load_samples():
    with transaction.manager:
        g_sadmin = GroupPermission(perm_name="system.admin")
        g_radmin = GroupPermission(perm_name="retailer.admin")
        g_edit = GroupPermission(perm_name="edit")
        g_view = GroupPermission(perm_name="view")
        g_order = GroupPermission(perm_name="order")

        group = Group(group_name="System Admins",
            permissions=[g_sadmin]).save()

        admin = User(user_name="admin", status=1, groups=[group],
            email="endre.karlson@gmail.com",
            first_name="Endre", last_name="Karlson")
        admin.set_password("admin")
        admin.save()



        # NOTE: First Retailer rents out cars and transport class cars
        customer = Customer(name="WreckRenters Inc", organisation_id=2343,
                    contact="Steffen Soma", email="stefsoma@gmail.com",
                    phone="+47 xxxxxxxx")

        group = Group(
            group_name="RentOurWrecks Inc",
            permissions=[g_radmin],
            organisation_id=3232,
            customers=[customer]).save()

        user = User(user_name="booker1", status=1, groups=[group],
                    email="booker1@random.com")
        user.set_password("booker1")
        user.save()

        sub_cars = category_dict(["Sedan", "Stationwagon", "SUV", "Coupe",
                            "Pickup", "7 seats", "9 seats"])
        top_cars = Category(name="Cars", categories=sub_cars.values()).save()
        sub_transport = category_dict(["Caddy", "6m 3", "11 m3", "18 m3"])
        top_transport = Category(name="Transport",
                                categories=sub_transport.values()).save()
        resources = Resource(
            resource_name="Cars", categories=[top_cars, top_transport],
            resource_type="categories").save()

        entity = DrivableEntity(
            brand="Mitsubishi",
            model="Lancer",
            identifier="DL87162",
            produced=2008,
            categories=[sub_cars["SUV"]]).save()
        entity = DrivableEntity(
            brand="Hyundai",
            model="Elantra",
            identifier="RH73369",
            produced=2000,
            categories=[sub_cars["Stationwagon"]]).save()

        # NOTE: Rents out Trucks and Bus
        customer = Customer(name="WreckLovers Inc", organisation_id=2343,
                contact="Endre Karlson", email="endre.karlson@gmail.com",
                phone="+47 xxxxxxxx")

        group = Group(
            group_name="TransportVehicles Inc",
            users=[user],
            organisation_id=3232,
            permissions=[g_radmin],
            customers=[customer]).save()

        user = User(user_name="booker2", status=1, groups=[group],
                    email="booker2@random.com").save()
        user.set_password("booker2")
        user.save()

        user = User(user_name="steffen", status=1, groups=[group],
                    first_name="Steffen", middle_name="Tenold",
                    last_name="Soma",
                    email="steffen.soma@gmail.com").save()
        user.set_password("password")
        user.save()

        sub_truck = category_dict(["18 m3", "22 m3", "26 m3", "35 m3"])
        top_truck = Category(name="Truck", categories=sub_truck.values()).save()
        sub_bus = category_dict(["9 seats", "17 seats"])
        top_bus = Category(name="Mini bus", categories=sub_bus.values()).save()
        resources = Resource(
            resource_name="Transport", categories=[top_truck, top_bus],
            resource_type="categories").save()

        entity = DrivableEntity(
            brand="Brand-A",
            model="Model-A",
            identifier="ID-A",
            produced=2004,
            categories=[sub_truck["18 m3"]]).save()
        entity = DrivableEntity(
            brand="Brand-B",
            model="Model-B",
            identifier="ID-B",
            produced=2011,
            categories=[sub_bus["9 seats"]]).save()

