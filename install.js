module.exports = {
  run: [
    // Clone the Image Resizer repository
    {
      method: "shell.run",
      params: {
        message: [
          "git clone https://github.com/Arnold2006/Image_Resizer.git app",
        ]
      }
    },
    // Install Python dependencies
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "uv pip install Pillow customtkinter tkinterdnd2",
        ]
      }
    },
  ]
}
