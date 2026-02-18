module.exports = {
  // daemon: false — this is a desktop GUI app, not a persistent server.
  // The script will naturally exit when the user closes the app window.
  run: [
    {
      method: "shell.run",
      params: {
        venv: "env",    // virtual environment folder
        path: "app",    // run from inside the cloned repo
        message: [
          "python app.py",
        ],
      }
    },
  ]
}
