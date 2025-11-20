from typing import Dict, Any, Optional, Literal
import os

import click
from mcp.server.fastmcp import FastMCP

from mcp_server_requests.version import __version__
from mcp_server_requests.request import mcp_http_request
from mcp_server_requests.ua import list_ua_browsers, list_ua_oses, random_ua
from mcp_server_requests.utils import parse


def get_user_agent(
    *,
    ua: str | None = None,
    ua_random: bool = False,
    ua_os: str | None = None,
    ua_browser: str | None = None,
) -> str:
    if not ua and ua_random:
        ua = random_ua(browser=ua_browser, os=ua_os)
        if not ua:
            raise RuntimeError(f"can't find suitable user-agent, os or browser: {ua_os}, {ua_browser}, try a different combination.")

    if not ua:
        ua = f"Mozilla/5.0 (compatible; mcp-server-requests/{__version__})"

    return ua


def create_mcp_server(
    *,
    ua: str | None = None,
    ua_random: bool = False,
    ua_os: str | None = None,
    ua_browser: str | None = None,
    ua_force: bool | None = None,
) -> FastMCP:

    mcp = FastMCP("Requests", log_level="ERROR")

    ua = get_user_agent(ua=ua, ua_random=ua_random, ua_os=ua_os, ua_browser=ua_browser)

    @mcp.tool()
    def fetch(url: str, *, return_content: Literal['raw', 'basic_clean', 'strict_clean', 'markdown'] = "markdown") -> str:
        """Fetch web page content.
        - If HTML, returns content based on return_content parameter.
        - If not HTML but text or JSON, returns the content directly.
        - If other content type, returns an error message.

        Args:
            url (str): The URL of the web page to fetch.
            return_content ("raw" | "basic_clean" | "strict_clean" | "markdown", optional): Defaults to "markdown". Controls how HTML content is returned:
                - raw: Returns original HTML content.
                - basic_clean: Returns filtered HTML content with non-visible tags removed (script, style, etc.).
                - strict_clean: Returns filtered HTML content with non-visible tags removed and most unnecessary HTML attributes deleted.
                - markdown: Converts HTML to Markdown before returning.

        Returns:
            - If return_content is raw: original HTML content.
            - If return_content is basic_clean: filtered HTML content with non-visible tags removed (script, style, etc.).
            - If return_content is strict_clean: filtered HTML content with non-visible tags removed and most unnecessary HTML attributes deleted.
            - If return_content is markdown: HTML converted to Markdown.
        """
        return mcp_http_request("GET", url, return_content=return_content, user_agent=ua, force_user_agnet=ua_force, format_headers=False)

    @mcp.tool()
    def fetch_to_file(
        url: str,
        file_path: str,
        *,
        return_content: Literal['raw', 'basic_clean', 'strict_clean', 'markdown'] = "markdown"
    ) -> str:
        """Fetch web page content and save to file.
        - If HTML, saves content based on return_content parameter.
        - If not HTML but text or JSON, saves the content directly.
        - If other content type, returns an error message.

        Args:
            url (str): The URL of the web page to fetch.
            file_path (str): The file path to save to. Must be an absolute path.
            return_content ("raw" | "basic_clean" | "strict_clean" | "markdown", optional): Defaults to "markdown". Controls how HTML content is returned:
                - raw: Returns original HTML content.
                - basic_clean: Returns filtered HTML content with non-visible tags removed (script, style, etc.).
                - strict_clean: Returns filtered HTML content with non-visible tags removed and most unnecessary HTML attributes deleted.
                - markdown: Converts HTML to Markdown before returning.

        Returns:
            - On success: file path where content was saved.
            - On error: error message if path is unsafe.
        """
        # Set protected paths based on operating system
        protected_paths = []
        if os.name == 'nt':  # Windows
            protected_paths.extend([
                os.path.join('C:', 'Windows'),
                os.path.join('C:', 'Program Files'),
                os.path.join('C:', 'Program Files (x86)'),
            ])
        else:  # Linux/Mac
            protected_paths.extend([
                '/etc',
                '/usr',
                '/bin',
                '/sbin',
                '/lib',
                '/root',
            ])

        if not os.path.isabs(file_path):
            return f"Error: Path must be absolute: {file_path}"

        # Check path safety
        file_path = os.path.abspath(file_path)
        for protected in protected_paths:
            if file_path.startswith(protected):
                return f"Error: Do not allow writing to protected paths: {protected}"

        # Fetch content
        content = mcp_http_request("GET", url, return_content=return_content,
                                   user_agent=ua, force_user_agnet=ua_force,
                                   format_headers=False)

        # Write to file
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"File written successfully to: {file_path}"

    @mcp.tool()
    def http_get(
        url: str,
        *,
        query: Optional[Dict[str, str | int | float]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """Execute HTTP GET request.

        Args:
            url (str): The target URL for the request.
            query (Dict[str, str | int | float], optional): Query parameter key-value pairs. Values are automatically converted to strings and appended to the URL.
                Example: {'key1': 'value1', 'key2': 2} is converted to key1=value1&key2=2 and appended to the URL.
            headers (Dict[str, str], optional): Custom HTTP request headers.

        Returns:
            str: Standard HTTP response format string containing status line, response headers, and response body.
        """
        return mcp_http_request("GET", url, query=query, headers=headers, user_agent=ua, force_user_agnet=ua_force)

    @mcp.tool()
    def http_post(
        url: str,
        *,
        query: Optional[Dict[str, str | int | float]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        json: Optional[Any] = None,
    ) -> str:
        """Execute HTTP POST request.

        Args:
            url (str): The target URL for the request.
            query (Dict[str, str | int | float], optional): Query parameter key-value pairs. Values are automatically converted to strings and appended to the URL.
                Example: {'key1': 'value1', 'key2': 2} is converted to key1=value1&key2=2 and appended to the URL.
            headers (Dict[str, str], optional): Custom HTTP request headers.
            data (str, optional): HTTP request body data as text. Cannot be used together with json parameter.
            json (Any, optional): HTTP request body data as JSON. Will be automatically serialized to JSON string. Cannot be used together with data parameter.

        Returns:
            str: Standard HTTP response format string containing status line, response headers, and response body.
        """
        return mcp_http_request("POST", url, query=query, data=data, json=json, headers=headers, user_agent=ua, force_user_agnet=ua_force)

    @mcp.tool()
    def http_put(
        url: str,
        *,
        query: Optional[Dict[str, str | int | float]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        json: Optional[Any] = None,
    ) -> str:
        """Execute HTTP PUT request.

        Args:
            url (str): The target URL for the request.
            query (Dict[str, str | int | float], optional): Query parameter key-value pairs. Values are automatically converted to strings and appended to the URL.
                Example: {'key1': 'value1', 'key2': 2} is converted to key1=value1&key2=2 and appended to the URL.
            headers (Dict[str, str], optional): Custom HTTP request headers.
            data (str, optional): HTTP request body data as text. Cannot be used together with json parameter.
            json (Any, optional): HTTP request body data as JSON. Will be automatically serialized to JSON string. Cannot be used together with data parameter.

        Returns:
            str: Standard HTTP response format string containing status line, response headers, and response body.
        """
        return mcp_http_request("PUT", url, query=query, data=data, json=json, headers=headers, user_agent=ua, force_user_agnet=ua_force)

    @mcp.tool()
    def http_patch(
        url: str,
        *,
        query: Optional[Dict[str, str | int | float]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        json: Optional[Any] = None,
    ) -> str:
        """Execute HTTP PATCH request.

        Args:
            url (str): The target URL for the request.
            query (Dict[str, str | int | float], optional): Query parameter key-value pairs. Values are automatically converted to strings and appended to the URL.
                Example: {'key1': 'value1', 'key2': 2} is converted to key1=value1&key2=2 and appended to the URL.
            headers (Dict[str, str], optional): Custom HTTP request headers.
            data (str, optional): HTTP request body data as text. Cannot be used together with json parameter.
            json (Any, optional): HTTP request body data as JSON. Will be automatically serialized to JSON string. Cannot be used together with data parameter.

        Returns:
            str: Standard HTTP response format string containing status line, response headers, and response body.
        """
        return mcp_http_request("PATCH", url, query=query, data=data, json=json, headers=headers, user_agent=ua, force_user_agnet=ua_force)

    @mcp.tool()
    def http_delete(
        url: str,
        *,
        query: Optional[Dict[str, str | int | float]] = None,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[str] = None,
        json: Optional[Any] = None,
    ) -> str:
        """Execute HTTP DELETE request.

        Args:
            url (str): The target URL for the request.
            query (Dict[str, str | int | float], optional): Query parameter key-value pairs. Values are automatically converted to strings and appended to the URL.
                Example: {'key1': 'value1', 'key2': 2} is converted to key1=value1&key2=2 and appended to the URL.
            headers (Dict[str, str], optional): Custom HTTP request headers.
            data (str, optional): HTTP request body data as text. Cannot be used together with json parameter.
            json (Any, optional): HTTP request body data as JSON. Will be automatically serialized to JSON string. Cannot be used together with data parameter.

        Returns:
            str: Standard HTTP response format string containing status line, response headers, and response body.
        """
        return mcp_http_request("DELETE", url, query=query, data=data, json=json, headers=headers, user_agent=ua, force_user_agnet=ua_force)

    return mcp


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--user-agent", default=None, help='Specify user agent string directly')
@click.option("--random-user-agent", is_flag=True, flag_value=True, default=None, help="Use a random user agent,")
@click.option("--force-user-agent", is_flag=True, help="Force the use of specified or randomly generated UA, ignoring UA provided by the model")
@click.option('--list-os-and-browser', is_flag=True, help='List available browsers and operating systems for UA selection')
def main(
    context: click.Context,
    user_agent: Optional[str],
    random_user_agent: Optional[str],
    force_user_agent: Optional[bool],
    list_os_and_browser: bool
):
    if list_os_and_browser and context.invoked_subcommand:
        raise ValueError("Cannot use --list-os-and-browser with subcommand.")
    if user_agent and random_user_agent:
        raise ValueError("Cannot use both --user-agent and --random-user-agent.")

    if list_os_and_browser:
        click.echo("Available browsers:")
        for b in sorted(list_ua_browsers()):
            click.echo(f"- {b}")
        click.echo("Available operating systems:")
        for o in sorted(list_ua_oses()):
            click.echo(f"- {o}")
        return

    if context.invoked_subcommand:
        pass
    else:
        ua_random = False
        ua_os = None
        ua_browser = None
        if isinstance(random_user_agent, str):
            limit = parse(random_user_agent)
            ua_random = True
            ua_os = limit.get("os", None)
            ua_browser = limit.get("browser", None)

        mcp = create_mcp_server(
            ua=user_agent,
            ua_random=ua_random,
            ua_os=ua_os,
            ua_browser=ua_browser,
            ua_force=force_user_agent,
        )
        mcp.run()


@main.command()
@click.argument("url", type=str, required=True)
@click.option("--return-content", type=click.Choice(['raw', 'basic_clean', 'strict_clean', 'markdown']), default="markdown", help="return content type")
def fetch(
    url: str,
    return_content: Literal['raw'] | Literal['basic_clean'] | Literal['strict_clean'] | Literal['markdown']
):
    res = mcp_http_request("GET", url, format_headers=False, return_content=return_content)
    click.echo(res)


@main.command()
@click.argument("url", type=str, required=True)
@click.option("--headers", type=str, default="", help="custom headers")
def get(url: str, headers: str):
    hs = parse(headers)
    res = mcp_http_request("GET", url, headers=hs)
    click.echo(res)


@main.command()
@click.argument("url", type=str, required=True)
@click.option("--headers", type=str, default="", help="custom headers")
@click.option("--data", type=str)
def post(url: str, headers: str, data: str | None):
    hs = parse(headers)
    res = mcp_http_request("POST", url, headers=hs, data=data)
    click.echo(res)


@main.command()
@click.argument("url", type=str, required=True)
@click.option("--headers", type=str, default="", help="custom headers")
@click.option("--data", type=str)
def put(url: str, headers: str, data: str | None):
    hs = parse(headers)
    res = mcp_http_request("PUT", url, headers=hs, data=data)
    click.echo(res)


@main.command()
@click.argument("url", type=str, required=True)
@click.option("--headers", type=str, default="", help="custom headers")
@click.option("--data", type=str)
def delete(url: str, headers: str, data: str | None):
    hs = parse(headers)
    res = mcp_http_request("DELETE", url, headers=hs, data=data)
    click.echo(res)


@main.command(help="not implemented yet")
@click.argument("query", type=str, required=True)
def search(query):
    raise NotImplementedError("Search functionality is not implemented yet")


if __name__ == "__main__":
    main()
