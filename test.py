import ssl
import socket

hostname = 'www.yahoo.com'
port = 443

context = ssl.create_default_context()
with socket.create_connection((hostname, port)) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        print(ssock.version())
        cipher = ssock.cipher()
        print(cipher)
        key_exchange = cipher[0].split("-")[0]
        print(key_exchange)
import http.client

def is_domain_support_h2(domain):
    try:
        import h2.connection
        import socket
        import ssl
        context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
        context.options |= ssl.OP_NO_COMPRESSION
        context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
        context.set_alpn_protocols(["h2"])
        with socket.create_connection((domain, port)) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                return ssock.version()=="TLSv1.3"
    except:
        return False

print(is_domain_support_h2(hostname))
# Check if ALPN is supported by the SSL module
if not ssl.HAS_ALPN:
    print("ALPN not supported")
    exit()

context = ssl.create_default_context()
context.set_alpn_protocols(["h2","http/1.1"])
conn = http.client.HTTPSConnection(hostname, port, context=context)
conn.request('GET', '/')
resp = conn.getresponse()

if resp.version == 11:
    print("HTTP/1.1")
elif resp.version == 20:
    print("HTTP/2")
else:
    print("Unknown protocol")

# Check the server's response headers for the HTTP2-Settings header
headers = resp.getheaders()
http2_settings = [h for h in headers if h[0].lower() == 'http2-settings']
if http2_settings:
    print("HTTP/2 supported (HTTP2-Settings found)")
else:
    print("HTTP/2 not supported (HTTP2-Settings not found)")




# -*- coding: utf-8 -*-
"""
Client HTTPS Setup
~~~~~~~~~~~~~~~~~

This example code fragment demonstrates how to set up a HTTP/2 client that
negotiates HTTP/2 using NPN and ALPN. For the sake of maximum explanatory value
this code uses the synchronous, low-level sockets API: however, if you're not
using sockets directly (e.g. because you're using asyncio), you should focus on
the set up required for the SSLContext object. For other concurrency libraries
you may need to use other setup (e.g. for Twisted you'll need to use
IProtocolNegotiationFactory).

This code requires Python 3.5 or later.
"""
import h2.connection
import socket
import ssl


def establish_tcp_connection():
    """
    This function establishes a client-side TCP connection. How it works isn't
    very important to this example. For the purpose of this example we connect
    to localhost.
    """
    return socket.create_connection((hostname, 443))


def get_http2_ssl_context():
    """
    This function creates an SSLContext object that is suitably configured for
    HTTP/2. If you're working with Python TLS directly, you'll want to do the
    exact same setup as this function does.
    """
    # Get the basic context from the standard library.
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)

    # RFC 7540 Section 9.2: Implementations of HTTP/2 MUST use TLS version 1.2
    # or higher. Disable TLS 1.1 and lower.
    ctx.options |= (
        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    )

    # RFC 7540 Section 9.2.1: A deployment of HTTP/2 over TLS 1.2 MUST disable
    # compression.
    ctx.options |= ssl.OP_NO_COMPRESSION

    # RFC 7540 Section 9.2.2: "deployments of HTTP/2 that use TLS 1.2 MUST
    # support TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256". In practice, the
    # blocklist defined in this section allows only the AES GCM and ChaCha20
    # cipher suites with ephemeral key negotiation.
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")

    # We want to negotiate using NPN and ALPN. ALPN is mandatory, but NPN may
    # be absent, so allow that. This setup allows for negotiation of HTTP/1.1.
    ctx.set_alpn_protocols(["h2"])

    try:
        ctx.set_npn_protocols(["h2"])
    except NotImplementedError:
        pass

    return ctx


def negotiate_tls(tcp_conn, context):
    """
    Given an established TCP connection and a HTTP/2-appropriate TLS context,
    this function:

    1. wraps TLS around the TCP connection.
    2. confirms that HTTP/2 was negotiated and, if it was not, throws an error.
    """
    # Note that SNI is mandatory for HTTP/2, so you *must* pass the
    # server_hostname argument.
    tls_conn = context.wrap_socket(tcp_conn, server_hostname=hostname)

    # Always prefer the result from ALPN to that from NPN.
    # You can only check what protocol was negotiated once the handshake is
    # complete.
    negotiated_protocol = tls_conn.selected_alpn_protocol()
    if negotiated_protocol is None:
        negotiated_protocol = tls_conn.selected_npn_protocol()

    if negotiated_protocol != "h2":
        raise RuntimeError("Didn't negotiate HTTP/2!")

    return tls_conn

if 1:
    # Step 1: Set up your TLS context.
    context = get_http2_ssl_context()

    # Step 2: Create a TCP connection.
    connection = establish_tcp_connection()

    # Step 3: W	rap the connection in TLS and validate that we negotiated HTTP/2
    tls_connection = negotiate_tls(connection, context)

