from typing import List

import click
import httpx
from click import ClickException
from pydantic import ValidationError
from scim2_client import SCIMClientError
from scim2_models import SearchRequest
from sphinx_click.rst_to_ansi_formatter import make_rst_to_ansi_formatter

from .utils import DOC_URL
from .utils import formatted_payload


@click.command(cls=make_rst_to_ansi_formatter(DOC_URL), name="search")
@click.pass_context
@click.option(
    "--attribute",
    multiple=True,
    help="A multi-valued list of strings indicating the names of resource attributes to return in the response, overriding the set of attributes that would be returned by default.",
)
@click.option(
    "--excluded-attribute",
    multiple=True,
    help="A multi-valued list of strings indicating the names of resource attributes to be removed from the default set of attributes to return.",
)
@click.option(
    "--start-index",
    type=int,
    help="An integer indicating the 1-based index of the first query result.",
)
@click.option(
    "--count",
    type=int,
    help="An integer indicating the desired maximum number of query results per page.",
)
@click.option(
    "--filter", help="The filter string used to request a subset of resources."
)
@click.option(
    "--sort-by",
    help="A string indicating the attribute whose value SHALL be used to order the returned responses.",
)
@click.option(
    "--sort-order",
    help="A string indicating the order in which the “sortBy” parameter is applied.",
)
@click.option(
    "--indent/--no-indent",
    is_flag=True,
    default=True,
    help="Indent JSON response payloads.",
)
def search_cli(
    ctx,
    attribute: List[str],
    excluded_attribute: List[str],
    start_index: int,
    count: int,
    filter: str,
    sort_by: str,
    sort_order: str,
    indent: bool,
):
    """Perform a `SCIM GET <https://www.rfc-editor.org/rfc/rfc7644#section-3.4.1>`_ request
    on the :code:`/.search` endpoint.

    Data passed in JSON format to stdin is sent as request arguments and all the other query arguments are ignored:

    .. code-block:: bash

        echo '{"startIndex": 50, "count": 10}' | scim https://scim.example search user
    """

    if ctx.obj.get("stdin"):
        check_request_payload = False
        payload = ctx.obj.get("stdin")

    else:
        check_request_payload = True
        payload = SearchRequest(
            attributes=attribute,
            excluded_attributes=excluded_attribute,
            start_index=start_index,
            count=count,
            filter=filter,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    try:
        response = ctx.obj["client"].search(
            search_request=payload,
            check_request_payload=check_request_payload,
        )

    except (httpx.HTTPError, SCIMClientError) as exc:
        raise ClickException(exc) from exc

    except ValidationError as exc:
        payload = formatted_payload(exc.response_payload, indent)
        message = f"The server response is invalid:\n{payload}\n{exc}"
        raise ClickException(message) from exc

    payload = formatted_payload(response.model_dump(), indent)
    click.echo(payload)