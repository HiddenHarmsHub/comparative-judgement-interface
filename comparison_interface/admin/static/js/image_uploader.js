FilePond.registerPlugin(
    FilePondPluginFileValidateSize,
  );

  token = document.querySelector('input[name="csrf_token"]').getAttribute("value");

  FilePond.setOptions({
    maxFileSize: "4MB",
    acceptedFileTypes: ["image/png", "image/jpeg"],

    server: {
        headers: { "X-CSRF-TOKEN": token },

        process: "./process",
        revert: "./revert",
        // load: {
        //     url: "../",
        // }
    },
  });
  
  // Select the file input and use 
  // create() to turn it into a pond
  FilePond.create(
    document.querySelector('input.filepond')
  );

   