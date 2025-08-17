class Attachment {
  final String id;
  final String fileName;
  final String fileUrl;
  final String fileType;

  Attachment({
    required this.id,
    required this.fileName,
    required this.fileUrl,
    required this.fileType,
  });

  factory Attachment.fromJson(Map<String, dynamic> json) {
    return Attachment(
      id: json['id'],
      fileName: json['file_name'],
      fileUrl: json['file_url'],
      fileType: json['file_type'],
    );
  }
}
