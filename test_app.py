"""
Test script to verify Flask app loads correctly
"""
try:
    from app import app
    print('[OK] Flask app loaded successfully')
    print('\nChecking new theme builder routes:')

    theme_routes = [rule for rule in app.url_map.iter_rules() if 'theme' in rule.rule.lower()]
    for route in theme_routes:
        print(f'  {route.rule} -> {route.endpoint}')

    media_routes = [rule for rule in app.url_map.iter_rules() if 'media' in rule.rule.lower()]
    if media_routes:
        print('\nMedia routes:')
        for route in media_routes:
            print(f'  {route.rule} -> {route.endpoint}')

    print('\n[OK] All routes registered successfully')

except Exception as e:
    print(f'[ERROR] Failed to load app: {e}')
    import traceback
    traceback.print_exc()
