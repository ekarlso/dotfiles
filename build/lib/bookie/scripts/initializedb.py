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
        g_admin = GroupPermission(perm_name="admin")
        g_edit = GroupPermission(perm_name="edit")
        g_view = GroupPermission(perm_name="view")
        g_order = GroupPermission(perm_name="order")

        # NOTE: First Retailer rents out cars and transport class cars
        customer = Customer(name="WreckRenters Inc", organisation_id=2343,
                    contact="Steffen Soma", email="stefsoma@gmail.com",
                    phone="+47 xxxxxxxx")

        user = User(user_name="booker1", status=1,
                    email="endre.karlson@gmail.com")
        user.set_password("booker1")
        user.save()

        group = Group(
            group_name="RentOurWrecks Inc",
            users=[user],
            permissions=[g_admin],
            organisation_id=3232,
            customers=[customer]).save()


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

        user = User(user_name="booker2", status=1,
                    email="endre.karlson@bouvet.no").save()
        user.set_password("admin")
        user.save()

        group = Group(
            group_name="TransportVehicles Inc",
            users=[user],
            organisation_id=3232,
            permissions=[g_admin],
            customers=[customer]).save()

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

