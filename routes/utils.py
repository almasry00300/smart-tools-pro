import requests

SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_DsdesyOGwBszyysrtoFrgg_pWHepUJy"

def save_site_config(settings):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicate"
    }
    try:
        requests.post(f"{SUPABASE_URL}/rest/v1/site_content", json=settings, headers=headers, timeout=5)
    except: pass

def get_site_config():
    headers = { "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}" }
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/site_content?select=*", headers=headers, timeout=5).json()
        if res: return res
    except: pass
    return {
        "header_color": "#ea580c", "card_color": "#f1f5f9", "bg_color": "#ffffff",
        "fb_url": "#", "tw_url": "#", "yt_url": "#", "tt_url": "#", "ig_url": "#", "tg_url": "#"
    }
