const HttpClient = (() => {
  async function request(path, options = {}) {
    const response = await fetch(path, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    let data = null;
    const text = await response.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
    }

    if (!response.ok) {
      let message = "Something went wrong. Please try again.";
      if (data && data.detail) {
        if (Array.isArray(data.detail)) {
          message = data.detail.map((item) => item.msg || item).join(" ");
        } else if (typeof data.detail === "string") {
          message = data.detail;
        } else {
          message = JSON.stringify(data.detail);
        }
      }
      throw new Error(message);
    }

    return data;
  }

  return { request };
})();
