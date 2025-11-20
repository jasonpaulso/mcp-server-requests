"""
MCP Server for HTTP requests with web scraping capabilities.
"""
from typing import Dict, Any, Optional, Literal
import os

from fastmcp import FastMCP

from mcp_server_requests.version import __version__
from mcp_server_requests.request import mcp_http_request


def create_server(
    *,
    ua: str | None = None,
    ua_random: bool = False,
    ua_os: str | None = None,
    ua_browser: str | None = None,
    ua_force: bool | None = None,
) -> FastMCP:
    """Create and configure the FastMCP server instance."""

    # Initialize FastMCP server
    mcp = FastMCP(
        name="Requests",
        instructions="HTTP client with web scraping capabilities. Supports GET, POST, PUT, PATCH, DELETE requests with optional HTML-to-Markdown conversion."
    )

    # Determine user agent
    user_agent = ua
    if not user_agent and ua_random:
        from mcp_server_requests.ua import random_ua
        user_agent = random_ua(browser=ua_browser, os=ua_os)
        if not user_agent:
            raise RuntimeError(
                f"Can't find suitable user-agent for os={ua_os}, browser={ua_browser}. "
                "Try a different combination."
            )

    if not user_agent:
        user_agent = f"Mozilla/5.0 (compatible; mcp-server-requests/{__version__})"

    # Tool definitions
    @mcp.tool()
    def fetch(
        url: str,
        *,
        return_content: Literal['raw', 'basic_clean', 'strict_clean', 'markdown'] = "markdown"
    ) -> str:
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
        return mcp_http_request(
            "GET", url,
            return_content=return_content,
            user_agent=user_agent,
            force_user_agnet=ua_force,
            format_headers=False
        )

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
        content = mcp_http_request(
            "GET", url,
            return_content=return_content,
            user_agent=user_agent,
            force_user_agnet=ua_force,
            format_headers=False
        )

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
        return mcp_http_request(
            "GET", url,
            query=query,
            headers=headers,
            user_agent=user_agent,
            force_user_agnet=ua_force
        )

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
        return mcp_http_request(
            "POST", url,
            query=query,
            data=data,
            json=json,
            headers=headers,
            user_agent=user_agent,
            force_user_agnet=ua_force
        )

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
        return mcp_http_request(
            "PUT", url,
            query=query,
            data=data,
            json=json,
            headers=headers,
            user_agent=user_agent,
            force_user_agnet=ua_force
        )

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
        return mcp_http_request(
            "PATCH", url,
            query=query,
            data=data,
            json=json,
            headers=headers,
            user_agent=user_agent,
            force_user_agnet=ua_force
        )

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
        return mcp_http_request(
            "DELETE", url,
            query=query,
            data=data,
            json=json,
            headers=headers,
            user_agent=user_agent,
            force_user_agnet=ua_force
        )

    return mcp


# Create default server instance
mcp = create_server()


if __name__ == "__main__":
    mcp.run()
