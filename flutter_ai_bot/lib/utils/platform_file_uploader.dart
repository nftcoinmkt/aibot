export 'platform_file_uploader_stub.dart';

export 'platform_file_uploader_io.dart' 
    if (dart.library.html) 'platform_file_uploader_web.dart';
