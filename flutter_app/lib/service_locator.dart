import 'package:get_it/get_it.dart';
import './services/get_host.dart';
import './services/localstorage_service.dart';

GetIt locator = GetIt();

Future<void> setupLocator() async {
    // locator.registerSingleton(Host());
    var instance = await LocalStorageService.getInstance();
    locator.registerSingleton<LocalStorageService>(instance);
}
