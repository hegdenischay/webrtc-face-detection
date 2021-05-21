import 'dart:async';
import 'dart:io';
import 'dart:core';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import 'services/localstorage_service.dart';
import 'dart:convert';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:flutter_native_image/flutter_native_image.dart';
import 'service_locator.dart';

class TakePictureScreen extends StatefulWidget {
  final CameraDescription camera;

  const TakePictureScreen({
    Key key,
    @required this.camera,
  }) : super(key: key);

  @override
  TakePictureScreenState createState() => TakePictureScreenState();
}

class TakePictureScreenState extends State<TakePictureScreen> {
  CameraController _controller;
  Future<void> _initializeControllerFuture;

  Future<String> _resizePhoto(String filePath) async {
      ImageProperties properties =
          await FlutterNativeImage.getImageProperties(filePath);

      int width = properties.width;
      var offset = (properties.height - properties.width) / 2;

      File croppedFile = await FlutterNativeImage.cropImage(
          filePath, 0, offset.round(), width, width);

      return croppedFile.path;
  }

  @override
  void initState() {
    super.initState();
    // To display the current output from the Camera,
    // create a CameraController.
    _controller = CameraController(
      // Get a specific camera from the list of available cameras.
      widget.camera,
      // Define the resolution to use.
      ResolutionPreset.medium,
    );

    // Next, initialize the controller. This returns a Future.
    _initializeControllerFuture = _controller.initialize();
  }

  @override
  void dispose() {
    // Dispose of the controller when the widget is disposed.
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Take a picture')),
      // Wait until the controller is initialized before displaying the
      // camera preview. Use a FutureBuilder to display a loading spinner
      // until the controller has finished initializing.
      body: FutureBuilder<void>(
        future: _initializeControllerFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.done) {
            // If the Future is complete, display the preview.
            return new Scaffold(
                body: new Container(
                    child: new AspectRatio(
                            aspectRatio: 1,
              child:  ClipRect(
              child: Transform.scale(
                scale: 1 / 1,
                child: Center(
                  child: AspectRatio(
                    aspectRatio: 1,
                    child: CameraPreview(_controller),
                  ),
                ),
              ),)
            )));
          } else {
            // Otherwise, display a loading indicator.
            return Center(child: CircularProgressIndicator());
          }
        },
      ),
      floatingActionButton: FloatingActionButton(
        child: Icon(Icons.camera_alt),
        // Provide an onPressed callback.
        onPressed: () async {
          // Take the Picture in a try / catch block. If anything goes wrong,
          // catch the error.
          try {
            // Ensure that the camera is initialized.
            await _initializeControllerFuture;

            // Attempt to take a picture and get the file `image`
            // where it was saved.
            final image = await _controller.takePicture();
            var host = LocalStorageService.getFromDisk('host');
            var postUri = Uri.parse("https://" + host + "/classify-remote");
            List<int> imageBytes = await image.readAsBytes();
            String bytes = UriData.fromBytes(imageBytes).toString();
    var localStorageService = locator<LocalStorageService>();

         var username = localStorageService.hasUser;
          print(username);
          var password = localStorageService.hasPass;
          print(password);
          Codec<String, String> stringtoBase64 = utf8.fuse(base64);
          String hash = stringtoBase64.encode(username + ":" + password);
          print(hash);
          print(postUri);
            // print("bytes read");
            http
                .post(
              postUri,
              headers: <String, String>{
                'Content-Type': 'application/json',
                'Authorization': 'Basic ' + hash,
              },
              body: jsonEncode(<String, String>{
                'data': bytes,
              }),
            )
                .then((response) {
              Fluttertoast.showToast(
                  msg: response.body == 'True'
                      ? 'Login Worked!'
                      : 'Login Failed!',
                  toastLength: Toast.LENGTH_SHORT,
                  gravity: ToastGravity.CENTER,
                  timeInSecForIosWeb: 1,
                  backgroundColor: Colors.red,
                  textColor: Colors.white,
                  fontSize: 16.0);

              // if (response.statusCode == 200) print("Uploaded!");
            });

            // If the picture was taken, display it on a new screen.
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => DisplayPictureScreen(
                  // Pass the automatically generated path to
                  // the DisplayPictureScreen widget.
                  imagePath: image?.path,
                ),
              ),
            );
          } catch (e) {
            // If an error occurs, log the error to the console.
            print(e);
          }
        },
      ),
    );
  }
}

// A widget that displays the picture taken by the user.
class DisplayPictureScreen extends StatelessWidget {
  final String imagePath;

  const DisplayPictureScreen({Key key, this.imagePath}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Display the Picture')),
      // The image is stored as a file on the device. Use the `Image.file`
      // constructor with the given path to display the image.
      body: Image.file(File(imagePath)),
    );
  }
}
