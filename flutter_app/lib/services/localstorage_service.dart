import 'package:shared_preferences/shared_preferences.dart';

class LocalStorageService {
  static LocalStorageService _instance;
  static SharedPreferences _preferences;
  var hostKey = 'host';
  var userKey = 'username';
  var passKey = 'password';
  static Future<LocalStorageService> getInstance() async {
    if (_instance == null) {
      _instance = LocalStorageService();
    }

    if (_preferences == null) {
      _preferences = await SharedPreferences.getInstance();
    }

    return _instance;
  }

  static getFromDisk(String key) {
    var value = _preferences.get(key);
    print('(TRACE) LocalStorageService:_getFromDisk. key: $key value: $value');
    return value;
  }

  static saveToDisk(String key, String content) {
    print(
        '(TRACE) LocalStorageService:_saveStringToDisk. key: $key value: $content');
    _preferences.setString(key, content);
  }

  String get hasHost => LocalStorageService.getFromDisk(hostKey) ?? 'unset';
  set hasHost(String value) => LocalStorageService.saveToDisk(hostKey, value);

  String get hasUser => LocalStorageService.getFromDisk(userKey) ?? 'unset';
  set hasUser(String value) => LocalStorageService.saveToDisk(userKey, value);

  String get hasPass => LocalStorageService.getFromDisk(passKey) ?? 'unset';
  set hasPass(String value) => LocalStorageService.saveToDisk(passKey, value);
}
