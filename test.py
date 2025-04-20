import winreg

def read_export_path_from_registry():
    try:
        key_path = r"SOFTWARE\Bytedance\CapCut\Modules\Export"
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        export_path, reg_type = winreg.QueryValueEx(registry_key, "ExportPath")
        winreg.CloseKey(registry_key)
        return export_path
    except FileNotFoundError:
        print("Không tìm thấy key hoặc giá trị ExportPath trong Registry.")
        return None
    except Exception as e:
        print(f"Lỗi khi đọc ExportPath: {e}")
        return None

def read_project_path_from_registry():
    try:
        key_path = r"SOFTWARE\Bytedance\CapCut\GlobalSettings\History"
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        project_path, reg_type = winreg.QueryValueEx(registry_key, "currentCustomDraftPath")
        winreg.CloseKey(registry_key)
        return project_path
    except FileNotFoundError:
        print("Không tìm thấy key hoặc giá trị currentCustomDraftPath trong Registry.")
        return None
    except Exception as e:
        print(f"Lỗi khi đọc currentCustomDraftPath: {e}")
        return None



print(read_export_path_from_registry())
print(read_project_path_from_registry())