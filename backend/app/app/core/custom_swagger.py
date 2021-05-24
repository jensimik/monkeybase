import json
from typing import Optional, Dict, Any
from fastapi.encoders import jsonable_encoder
from starlette.responses import HTMLResponse


def get_swagger_ui_html(
    *,
    openapi_url: str,
    title: str,
    swagger_js_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3.49.0/swagger-ui-bundle.js",
    swagger_css_url: str = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@3.49.0/swagger-ui.css",
    swagger_favicon_url: str = "https://fastapi.tiangolo.com/img/favicon.png",
    oauth2_redirect_url: Optional[str] = None,
    init_oauth: Optional[Dict[str, Any]] = None,
) -> HTMLResponse:
    """custom swagger with showing which scopes are required for each endpoint"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <link type="text/css" rel="stylesheet" href="{swagger_css_url}">
    <link rel="shortcut icon" href="{swagger_favicon_url}">
    <title>{title}</title>
    </head>
    <body>
    <div id="swagger-ui">
    </div>
    <script src="https://unpkg.com/react@15/dist/react.min.js"></script>
    <script src="{swagger_js_url}"></script>
    <!-- `SwaggerUIBundle` is now available on the page -->
    <script>
    const h = React.createElement
    const ui = SwaggerUIBundle({{
        url: '{openapi_url}',
    """

    if oauth2_redirect_url:
        html += f"oauth2RedirectUrl: window.location.origin + '{oauth2_redirect_url}',"

    html += """
        dom_id: '#swagger-ui',
        presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIBundle.SwaggerUIStandalonePreset,
        system => {
            // Variable to capture the security prop of OperationSummary
            // then pass it to authorizeOperationBtn
            let currentSecurity
            return {
                wrapComponents: {
                    // Wrap OperationSummary component to get its prop
                    OperationSummary: Original => props => {
                        const security = props.operationProps.get('security')
                        currentSecurity = security.toJS()
                        return h(Original, props)
                    },
                    // Wrap the padlock button to show the
                    // scopes required for current operation
                    authorizeOperationBtn: Original =>
                        function (props) {
                            return h('div', {}, [
                                ...(currentSecurity || []).map(scheme => {
                                    const schemeName = Object.keys(scheme)[0]
                                    if (!scheme[schemeName].length) return null

                                    const scopes = scheme[schemeName].flatMap(scope => [
                                        h('code', null, scope),
                                        ', ',
                                    ])
                                    scopes.pop()
                                    return h('span', null, [schemeName, '(', ...scopes, ')'])
                                }),
                                h(Original, props),
                            ])
                        },
                },
            }
        }
        ],
        layout: "BaseLayout",
        deepLinking: true,
        showExtensions: true,
        showCommonExtensions: true
    })"""

    if init_oauth:
        html += f"""
        ui.initOAuth({json.dumps(jsonable_encoder(init_oauth))})
        """

    html += """
    </script>
    </body>
    </html>
    """
    return HTMLResponse(html)
