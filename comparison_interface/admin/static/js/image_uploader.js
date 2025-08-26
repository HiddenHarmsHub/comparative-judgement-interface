FilePond.registerPlugin(
  FilePondPluginFileValidateSize,
  FilePondPluginFileValidateType,
);

$(function () {
  const fileList = [];
  $.get('./current-files').done(function (fileNames) {
    const data = JSON.parse(fileNames);
    const fileNameList = data.filenames.split('|');
    for (let i = 0; i < fileNameList.length; i += 1) {
      if (fileNameList[i] !== "") {
        let fileEntry = {
          source: fileNameList[i],
          options: {
            type: 'limbo',
          }
        };
        fileList.push(fileEntry);
      }
    }
    // create the pond with the file list
    FilePond.create(
      document.querySelector('input.filepond'),
      {
        files: fileList,
      }
    );
  });
});

FilePond.setOptions({
  maxFileSize: "4MB",
  acceptedFileTypes: ["image/png", "image/jpeg"],
  labelFileTypeNotAllowed: 'Only png and jpeg files can be uploaded',

  server: {
    headers: {"X-CSRF-TOKEN": document.querySelector('input[name="csrf_token"]').getAttribute("value")},
    process: "./process",
    revert: "./revert",
    load: "./load/",
  },
});
 