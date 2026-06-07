import json, logging, aiohttp, uuid
from aiohttp import web
from typing import Dict, Any

logger = logging.getLogger(__name__)

def setup_identity_routes(app, identity_manager, webauthn_manager, session_manager):
    async def oidc_discovery(request):
        base_url = f"{request.scheme}://{request.host}"
        return web.json_response(identity_manager.get_openid_configuration(base_url))

    async def oidc_jwks(request):
        return web.json_response(identity_manager.get_jwks())

    async def oidc_authorize(request):
        params = request.query
        client_id = params.get("client_id")
        redirect_uri = params.get("redirect_uri")
        scope = params.get("scope", "")
        state = params.get("state")
        nonce = params.get("nonce")
        user_id = params.get("user_id", "demo_user")
        if not client_id or not redirect_uri:
            raise web.HTTPBadRequest(text="Missing client_id or redirect_uri")
        code = identity_manager.create_authorization_code(client_id, redirect_uri, scope.split(), user_id, nonce)
        redirect_url = f"{redirect_uri}?code={code}"
        if state: redirect_url += f"&state={state}"
        raise web.HTTPFound(redirect_url)

    async def oidc_token(request):
        data = await request.post()
        grant_type = data.get("grant_type", "authorization_code")
        if grant_type == "authorization_code":
            code = data.get("code", "")
            client_id = data.get("client_id", "")
            client_secret = data.get("client_secret", "")
            redirect_uri = data.get("redirect_uri", "")
            if not identity_manager.authenticate_client(client_id, client_secret):
                raise web.HTTPUnauthorized(text="Invalid client credentials")
            auth_code = identity_manager.validate_authorization_code(code, client_id, redirect_uri)
            if not auth_code:
                raise web.HTTPBadRequest(text="Invalid authorization code")
            tokens = identity_manager.create_token_pair(client_id, auth_code.user_id, auth_code.scopes)
            return web.json_response(tokens)
        elif grant_type == "refresh_token":
            refresh_token = data.get("refresh_token", "")
            tokens = identity_manager.refresh_access_token(refresh_token)
            if not tokens:
                raise web.HTTPBadRequest(text="Invalid refresh token")
            return web.json_response(tokens)
        raise web.HTTPBadRequest(text="Unsupported grant type")

    async def oidc_userinfo(request):
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "")
        at = identity_manager.validate_access_token(token)
        if not at:
            raise web.HTTPUnauthorized(text="Invalid or expired token")
        user = identity_manager.get_user(at.user_id)
        if not user:
            raise web.HTTPNotFound(text="User not found")
        claims = {"sub": at.user_id}
        if "email" in at.scopes and user.get("email"): claims["email"] = user["email"]
        if "profile" in at.scopes:
            if user.get("name"): claims["name"] = user["name"]
            if user.get("preferred_username"): claims["preferred_username"] = user["preferred_username"]
        return web.json_response(claims)

    async def oidc_register(request):
        data = await request.json()
        client = identity_manager.register_client(
            data.get("redirect_uris", []), data.get("grant_types", ["authorization_code"]),
            data.get("scopes", ["openid", "profile"]), data.get("client_name", "Unnamed Client"))
        return web.json_response(client, status=201)

    async def webauthn_register_begin(request):
        data = await request.json()
        user_id = data.get("user_id", str(uuid.uuid4()))
        user_name = data.get("user_name", user_id)
        user_display = data.get("user_display_name", user_name)
        webauthn_manager.add_user(user_id, user_name, user_display)
        options = webauthn_manager.generate_registration_options(user_id, user_name, user_display)
        return web.json_response({"user_id": user_id, "options": options})

    async def webauthn_register_complete(request):
        data = await request.json()
        result = webauthn_manager.verify_registration(
            data["user_id"], data["challenge"], data["credential_id"],
            data["public_key"], data.get("device_name", "Unknown Device"),
            data.get("authenticator_type", "platform"), data.get("backed_up", False), data.get("sign_count", 0))
        return web.json_response({"verified": result})

    async def webauthn_login_begin(request):
        data = await request.json() if request.body_exists else {}
        options = webauthn_manager.generate_authentication_options(data.get("user_id"))
        return web.json_response({"options": options})

    async def webauthn_login_complete(request):
        data = await request.json()
        result = webauthn_manager.verify_authentication(
            data["user_id"], data["challenge"], data["credential_id"], data.get("sign_count", 0))
        if result:
            session = session_manager.create_session(data["user_id"], {
                "user_agent": request.headers.get("User-Agent", ""),
                "platform": request.headers.get("Sec-CH-UA-Platform", "unknown"),
                "ip_address": request.remote or request.headers.get("X-Forwarded-IP", "unknown"),
            }, auth_method="webauthn")
            return web.json_response({"verified": True, "session": session.to_dict()})
        return web.json_response({"verified": False}, status=401)

    async def webauthn_credentials(request):
        user_id = request.query.get("user_id", "")
        devices = webauthn_manager.get_user_devices(user_id)
        return web.json_response(devices)

    async def webauthn_delete_credential(request):
        user_id = request.query.get("user_id", "")
        credential_id = request.match_info.get("credential_id", "")
        result = webauthn_manager.remove_credential(user_id, credential_id)
        return web.json_response({"deleted": result})

    async def list_sessions(request):
        user_id = request.query.get("user_id", "")
        current = request.query.get("current_session_id")
        sessions = session_manager.get_user_sessions(user_id, current)
        return web.json_response(sessions)

    async def get_current_session(request):
        session_id = request.headers.get("X-Session-ID", "")
        session = session_manager.get_session(session_id)
        if not session: raise web.HTTPNotFound(text="Session not found")
        return web.json_response(session.to_dict())

    async def revoke_session(request):
        session_id = request.match_info.get("session_id", "")
        result = session_manager.revoke_session(session_id)
        return web.json_response({"revoked": result})

    async def revoke_all_sessions(request):
        user_id = request.query.get("user_id", "")
        exclude = request.query.get("exclude_session_id")
        count = session_manager.revoke_all_user_sessions(user_id, exclude)
        return web.json_response({"revoked_count": count})

    async def pam_request_access(request):
        data = await request.json()
        try:
            result = identity_manager.pam.request_access(
                data["user_id"], data["target_role"], data.get("duration_minutes", 60),
                data.get("reason", ""), data.get("resource_ids"),
                data.get("is_break_glass", False))
            return web.json_response(result)
        except ValueError:
            logger.warning("Invalid PAM access request payload", exc_info=True)
            raise web.HTTPBadRequest(text="Invalid request")

    async def pam_approve(request):
        data = await request.json()
        result = identity_manager.pam.approve_request(data["request_id"], data["approver_id"])
        if not result: raise web.HTTPNotFound(text="Request not found")
        return web.json_response(result)

    async def pam_deny(request):
        data = await request.json()
        result = identity_manager.pam.deny_request(data["request_id"], data["approver_id"], data.get("reason", ""))
        if not result: raise web.HTTPNotFound(text="Request not found")
        return web.json_response(result)

    async def pam_pending(request):
        user_id = request.query.get("user_id")
        requests_list = identity_manager.pam.get_pending_requests(user_id)
        return web.json_response(requests_list)

    async def pam_history(request):
        user_id = request.query.get("user_id")
        history = identity_manager.pam.get_request_history(user_id)
        return web.json_response(history)

    async def pam_recordings(request):
        recordings = identity_manager.pam.recorder.get_statistics()
        return web.json_response(recordings)

    app.router.add_get("/auth/oidc/.well-known/openid-configuration", oidc_discovery)
    app.router.add_get("/auth/oidc/jwks", oidc_jwks)
    app.router.add_get("/auth/oidc/authorize", oidc_authorize)
    app.router.add_post("/auth/oidc/token", oidc_token)
    app.router.add_get("/auth/oidc/userinfo", oidc_userinfo)
    app.router.add_post("/auth/oidc/register", oidc_register)
    app.router.add_post("/auth/webauthn/register/begin", webauthn_register_begin)
    app.router.add_post("/auth/webauthn/register/complete", webauthn_register_complete)
    app.router.add_post("/auth/webauthn/login/begin", webauthn_login_begin)
    app.router.add_post("/auth/webauthn/login/complete", webauthn_login_complete)
    app.router.add_get("/auth/webauthn/credentials", webauthn_credentials)
    app.router.add_delete("/auth/webauthn/credentials/{credential_id}", webauthn_delete_credential)
    app.router.add_get("/auth/sessions", list_sessions)
    app.router.add_get("/auth/sessions/current", get_current_session)
    app.router.add_delete("/auth/sessions/{session_id}", revoke_session)
    app.router.add_delete("/auth/sessions", revoke_all_sessions)
    app.router.add_post("/auth/pam/request", pam_request_access)
    app.router.add_post("/auth/pam/approve", pam_approve)
    app.router.add_post("/auth/pam/deny", pam_deny)
    app.router.add_get("/auth/pam/requests", pam_pending)
    app.router.add_get("/auth/pam/requests/history", pam_history)
    app.router.add_get("/auth/pam/sessions/recordings", pam_recordings)
    logger.info("Identity routes configured")
