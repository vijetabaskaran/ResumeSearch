print("Testing backend startup and imports...")
try:
    from app import app
    print("SUCCESS: All components and routers imported cleanly!")
except Exception as e:
    print("ERROR during import:")
    import traceback
    traceback.print_exc()
