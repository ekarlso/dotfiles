from webhelpers.html import grid, literal, tags
from webhelpers import date


from .navigation import get_nav_data


def wrap_td(string):
    return tags.HTML.td(literal(string))


def column_link(request, value, route, url_args=[], url_kw={}):
    """
    Helpers to format a element in a column as a anchor

    :param request: A Request object
    :param anchor_text: The text of the anchor
    :param route: The Route to use
    :key url_args: Args to pass down
    :key url_kw: Keywords to pass down
    """
    url_kw = get_nav_data(request, extra=url_kw)
    href = request.route_url(route, *url_args, **url_kw)
    anchor = tags.HTML.tag("a", href=href, c=value)
    return wrap_td(anchor)


def when_normalize(col_num, i, item):
    time = item.timestamp
    label = date.distance_of_time_in_words(time,
        datetime.utcnow(),
        granularity='minute')
    if item.request_id:
        href = request.route_url('logs',
            _query=(('request_id', item.request_id,),), page=1)
        return tags.HTML.td(h.link_to(label, href,
            title=time.strftime('%Y-%m-%d %H:%M:%S'),
            class_='c%s' % col_num))
    else:
       return tags.HTML.td(label, title=time.strftime('%Y-%m-%d %H:%M:%S'),
            class_='c%s' % col_num)


class PyramidGrid(grid.Grid):
    """
    Subclass of Grid that can handle header link generation for quick building
    of tables that support ordering of their contents, paginated results etc.
    """
    def generate_header_link(self, column_number, column, label_text):
        """
        This handles generation of link and then decides to call
        self.default_header_ordered_column_format or
        self.default_header_column_format based on if current column is the one
        that is used for sorting or not
        """

        # this will handle possible URL generation
        GET = dict(self.request.copy().GET) # needs dict() for py2.5 compat
        self.order_column = GET.pop("order_col", None)
        self.order_dir = GET.pop("order_dir", None)
        # determine new order
        if column == self.order_column and self.order_dir == "asc":
            new_order_dir = "dsc"
        else:
            new_order_dir = "asc"
        self.additional_kw['order_col'] = column
        self.additional_kw['order_dir'] = new_order_dir
        # generate new url
        new_url = self.url_generator(_query=self.additional_kw)
        # set label for header with link
        label_text = tags.HTML.tag("a", href=new_url, c=label_text)
        # Is the current column the one we're ordering on?
        if column == self.order_column:
            return self.default_header_ordered_column_format(column_number,
                                                             column,
                                                             label_text)
        else:
            return self.default_header_column_format(column_number, column,
                                                     label_text)

class PyramidObjectGrid(PyramidGrid):
    """
    This grid will work well with sqlalchemy row instances
    """
    def default_column_format(self, column_number, i, record, column_name):
        class_name = "c%s" % (column_number)
        return tags.HTML.tag("td", getattr(record, column_name), class_=class_name)
