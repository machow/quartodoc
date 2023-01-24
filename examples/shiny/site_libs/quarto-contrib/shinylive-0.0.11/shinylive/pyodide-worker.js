// Shinylive 0.0.11
// Copyright 2022 RStudio, PBC
var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __require = /* @__PURE__ */ ((x) => typeof require !== "undefined" ? require : typeof Proxy !== "undefined" ? new Proxy(x, {
  get: (a, b) => (typeof require !== "undefined" ? require : a)[b]
}) : x)(function(x) {
  if (typeof require !== "undefined")
    return require.apply(this, arguments);
  throw new Error('Dynamic require of "' + x + '" is not supported');
});
var __commonJS = (cb, mod) => function __require2() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));

// node_modules/ws/browser.js
var require_browser = __commonJS({
  "node_modules/ws/browser.js"(exports, module) {
    "use strict";
    module.exports = function() {
      throw new Error(
        "ws does not work in the browser. Browser clients must use the native WebSocket object"
      );
    };
  }
});

// src/awaitable-queue.ts
var AwaitableQueue = class {
  constructor() {
    this._buffer = [];
    this._resolve = null;
    this._promise = null;
    this._notifyAll();
  }
  async _wait() {
    await this._promise;
  }
  _notifyAll() {
    if (this._resolve) {
      this._resolve();
    }
    this._promise = new Promise((resolve) => this._resolve = resolve);
  }
  async dequeue() {
    while (this._buffer.length === 0) {
      await this._wait();
    }
    return this._buffer.shift();
  }
  enqueue(x) {
    this._buffer.push(x);
    this._notifyAll();
  }
};

// src/utils.ts
function uint8ArrayToString(buf) {
  let result = "";
  for (let i = 0; i < buf.length; i++) {
    result += String.fromCharCode(buf[i]);
  }
  return result;
}

// src/messageporthttp.ts
async function makeRequest(scope, appName, clientPort, pyodide2) {
  const asgiFunc = pyodide2.runPython(
    `_shiny_app_registry["${appName}"].app.call_pyodide`
  );
  await connect(scope, clientPort, asgiFunc);
}
async function connect(scope, clientPort, asgiFunc) {
  const fromClientQueue = new AwaitableQueue();
  clientPort.addEventListener("message", (event) => {
    if (event.data.type === "http.request") {
      fromClientQueue.enqueue({
        type: "http.request",
        body: event.data.body,
        more_body: event.data.more_body
      });
    }
  });
  clientPort.start();
  async function fromClient() {
    return fromClientQueue.dequeue();
  }
  async function toClient(event) {
    event = Object.fromEntries(event.toJs());
    if (event.type === "http.response.start") {
      clientPort.postMessage({
        type: event.type,
        status: event.status,
        headers: asgiHeadersToRecord(event.headers)
      });
    } else if (event.type === "http.response.body") {
      clientPort.postMessage({
        type: event.type,
        body: asgiBodyToArray(event.body),
        more_body: event.more_body
      });
    } else {
      throw new Error(`Unhandled ASGI event: ${event.type}`);
    }
  }
  await asgiFunc(scope, fromClient, toClient);
}
function asgiHeadersToRecord(headers) {
  headers = headers.map(([key, val]) => {
    return [uint8ArrayToString(key), uint8ArrayToString(val)];
  });
  return Object.fromEntries(headers);
}
function asgiBodyToArray(body) {
  return body;
}

// src/messageportwebsocket.ts
var MessagePortWebSocket = class extends EventTarget {
  constructor(port) {
    super();
    this.readyState = 0;
    this.addEventListener("open", (e) => {
      if (this.onopen) {
        this.onopen(e);
      }
    });
    this.addEventListener("message", (e) => {
      if (this.onmessage) {
        this.onmessage(e);
      }
    });
    this.addEventListener("error", (e) => {
      if (this.onerror) {
        this.onerror(e);
      }
    });
    this.addEventListener("close", (e) => {
      if (this.onclose) {
        this.onclose(e);
      }
    });
    this._port = port;
    port.addEventListener("message", this._onMessage.bind(this));
    port.start();
  }
  accept() {
    if (this.readyState !== 0) {
      return;
    }
    this.readyState = 1;
    this._port.postMessage({ type: "open" });
  }
  send(data) {
    if (this.readyState === 0) {
      throw new DOMException(
        "Can't send messages while WebSocket is in CONNECTING state",
        "InvalidStateError"
      );
    }
    if (this.readyState > 1) {
      return;
    }
    this._port.postMessage({ type: "message", value: { data } });
  }
  close(code, reason) {
    if (this.readyState > 1) {
      return;
    }
    this.readyState = 2;
    this._port.postMessage({ type: "close", value: { code, reason } });
    this.readyState = 3;
    this.dispatchEvent(new CloseEvent("close", { code, reason }));
  }
  _onMessage(e) {
    const event = e.data;
    switch (event.type) {
      case "open":
        if (this.readyState === 0) {
          this.readyState = 1;
          this.dispatchEvent(new Event("open"));
          return;
        }
        break;
      case "message":
        if (this.readyState === 1) {
          this.dispatchEvent(new MessageEvent("message", { ...event.value }));
          return;
        }
        break;
      case "close":
        if (this.readyState < 3) {
          this.readyState = 3;
          this.dispatchEvent(new CloseEvent("close", { ...event.value }));
          return;
        }
        break;
    }
    this._reportError(
      `Unexpected event '${event.type}' while in readyState ${this.readyState}`,
      1002
    );
  }
  _reportError(message, code) {
    this.dispatchEvent(new ErrorEvent("error", { message }));
    if (typeof code === "number") {
      this.close(code, message);
    }
  }
};

// src/messageportwebsocket-channel.ts
async function openChannel(path, appName, clientPort, pyodide2) {
  const conn = new MessagePortWebSocket(clientPort);
  const asgiFunc = pyodide2.runPython(
    `_shiny_app_registry["${appName}"].app.call_pyodide`
  );
  await connect2(path, conn, asgiFunc);
}
async function connect2(path, conn, asgiFunc) {
  const scope = {
    type: "websocket",
    asgi: {
      version: "3.0",
      spec_version: "2.1"
    },
    path,
    headers: []
  };
  const fromClientQueue = new AwaitableQueue();
  fromClientQueue.enqueue({ type: "websocket.connect" });
  async function fromClient() {
    return await fromClientQueue.dequeue();
  }
  async function toClient(event) {
    event = Object.fromEntries(event.toJs());
    if (event.type === "websocket.accept") {
      conn.accept();
    } else if (event.type === "websocket.send") {
      conn.send(event.text ?? event.bytes);
    } else if (event.type === "websocket.close") {
      conn.close(event.code, event.reason);
    } else {
      conn.close(1002, "ASGI protocol error");
      throw new Error(`Unhandled ASGI event: ${event.type}`);
    }
  }
  conn.addEventListener("message", (e) => {
    const me = e;
    const event = { type: "websocket.receive" };
    if (typeof me.data === "string") {
      event.text = me.data;
    } else {
      event.bytes = me.data;
    }
    fromClientQueue.enqueue(event);
  });
  conn.addEventListener("close", (e) => {
    const ce = e;
    fromClientQueue.enqueue({ type: "websocket.disconnect", code: ce.code });
  });
  conn.addEventListener("error", (e) => {
    console.error(e);
  });
  await asgiFunc(scope, fromClient, toClient);
}

// src/postable-error.ts
function errorToPostableErrorObject(e) {
  const errObj = {
    message: "An unknown error occured",
    name: e.name
  };
  if (!(e instanceof Error)) {
    return errObj;
  }
  errObj.message = e.message;
  if (e.stack) {
    errObj.stack = e.stack;
  }
  return errObj;
}

// src/pyodide/pyodide.js
var StackFrame;
var FIREFOX_SAFARI_STACK_REGEXP;
var CHROME_IE_STACK_REGEXP;
var SAFARI_NATIVE_CODE_REGEXP;
var errorStackParser = { exports: {} };
var stackframe = { exports: {} };
stackframe.exports = function() {
  function _isNumber(n) {
    return !isNaN(parseFloat(n)) && isFinite(n);
  }
  function _capitalize(str) {
    return str.charAt(0).toUpperCase() + str.substring(1);
  }
  function _getter(p) {
    return function() {
      return this[p];
    };
  }
  var booleanProps = ["isConstructor", "isEval", "isNative", "isToplevel"], numericProps = ["columnNumber", "lineNumber"], stringProps = ["fileName", "functionName", "source"], arrayProps = ["args"], objectProps = ["evalOrigin"], props = booleanProps.concat(numericProps, stringProps, arrayProps, objectProps);
  function StackFrame2(obj) {
    if (obj)
      for (var i2 = 0; i2 < props.length; i2++)
        void 0 !== obj[props[i2]] && this["set" + _capitalize(props[i2])](obj[props[i2]]);
  }
  StackFrame2.prototype = { getArgs: function() {
    return this.args;
  }, setArgs: function(v) {
    if ("[object Array]" !== Object.prototype.toString.call(v))
      throw new TypeError("Args must be an Array");
    this.args = v;
  }, getEvalOrigin: function() {
    return this.evalOrigin;
  }, setEvalOrigin: function(v) {
    if (v instanceof StackFrame2)
      this.evalOrigin = v;
    else {
      if (!(v instanceof Object))
        throw new TypeError("Eval Origin must be an Object or StackFrame");
      this.evalOrigin = new StackFrame2(v);
    }
  }, toString: function() {
    var fileName = this.getFileName() || "", lineNumber = this.getLineNumber() || "", columnNumber = this.getColumnNumber() || "", functionName = this.getFunctionName() || "";
    return this.getIsEval() ? fileName ? "[eval] (" + fileName + ":" + lineNumber + ":" + columnNumber + ")" : "[eval]:" + lineNumber + ":" + columnNumber : functionName ? functionName + " (" + fileName + ":" + lineNumber + ":" + columnNumber + ")" : fileName + ":" + lineNumber + ":" + columnNumber;
  } }, StackFrame2.fromString = function(str) {
    var argsStartIndex = str.indexOf("("), argsEndIndex = str.lastIndexOf(")"), functionName = str.substring(0, argsStartIndex), args = str.substring(argsStartIndex + 1, argsEndIndex).split(","), locationString = str.substring(argsEndIndex + 1);
    if (0 === locationString.indexOf("@"))
      var parts = /@(.+?)(?::(\d+))?(?::(\d+))?$/.exec(locationString, ""), fileName = parts[1], lineNumber = parts[2], columnNumber = parts[3];
    return new StackFrame2({ functionName, args: args || void 0, fileName, lineNumber: lineNumber || void 0, columnNumber: columnNumber || void 0 });
  };
  for (var i = 0; i < booleanProps.length; i++)
    StackFrame2.prototype["get" + _capitalize(booleanProps[i])] = _getter(booleanProps[i]), StackFrame2.prototype["set" + _capitalize(booleanProps[i])] = function(p) {
      return function(v) {
        this[p] = Boolean(v);
      };
    }(booleanProps[i]);
  for (var j = 0; j < numericProps.length; j++)
    StackFrame2.prototype["get" + _capitalize(numericProps[j])] = _getter(numericProps[j]), StackFrame2.prototype["set" + _capitalize(numericProps[j])] = function(p) {
      return function(v) {
        if (!_isNumber(v))
          throw new TypeError(p + " must be a Number");
        this[p] = Number(v);
      };
    }(numericProps[j]);
  for (var k = 0; k < stringProps.length; k++)
    StackFrame2.prototype["get" + _capitalize(stringProps[k])] = _getter(stringProps[k]), StackFrame2.prototype["set" + _capitalize(stringProps[k])] = function(p) {
      return function(v) {
        this[p] = String(v);
      };
    }(stringProps[k]);
  return StackFrame2;
}();
var ErrorStackParser = errorStackParser.exports = (StackFrame = stackframe.exports, FIREFOX_SAFARI_STACK_REGEXP = /(^|@)\S+:\d+/, CHROME_IE_STACK_REGEXP = /^\s*at .*(\S+:\d+|\(native\))/m, SAFARI_NATIVE_CODE_REGEXP = /^(eval@)?(\[native code])?$/, { parse: function(error) {
  if (void 0 !== error.stacktrace || void 0 !== error["opera#sourceloc"])
    return this.parseOpera(error);
  if (error.stack && error.stack.match(CHROME_IE_STACK_REGEXP))
    return this.parseV8OrIE(error);
  if (error.stack)
    return this.parseFFOrSafari(error);
  throw new Error("Cannot parse given Error object");
}, extractLocation: function(urlLike) {
  if (-1 === urlLike.indexOf(":"))
    return [urlLike];
  var parts = /(.+?)(?::(\d+))?(?::(\d+))?$/.exec(urlLike.replace(/[()]/g, ""));
  return [parts[1], parts[2] || void 0, parts[3] || void 0];
}, parseV8OrIE: function(error) {
  return error.stack.split("\n").filter(function(line) {
    return !!line.match(CHROME_IE_STACK_REGEXP);
  }, this).map(function(line) {
    line.indexOf("(eval ") > -1 && (line = line.replace(/eval code/g, "eval").replace(/(\(eval at [^()]*)|(,.*$)/g, ""));
    var sanitizedLine = line.replace(/^\s+/, "").replace(/\(eval code/g, "(").replace(/^.*?\s+/, ""), location2 = sanitizedLine.match(/ (\(.+\)$)/);
    sanitizedLine = location2 ? sanitizedLine.replace(location2[0], "") : sanitizedLine;
    var locationParts = this.extractLocation(location2 ? location2[1] : sanitizedLine), functionName = location2 && sanitizedLine || void 0, fileName = ["eval", "<anonymous>"].indexOf(locationParts[0]) > -1 ? void 0 : locationParts[0];
    return new StackFrame({ functionName, fileName, lineNumber: locationParts[1], columnNumber: locationParts[2], source: line });
  }, this);
}, parseFFOrSafari: function(error) {
  return error.stack.split("\n").filter(function(line) {
    return !line.match(SAFARI_NATIVE_CODE_REGEXP);
  }, this).map(function(line) {
    if (line.indexOf(" > eval") > -1 && (line = line.replace(/ line (\d+)(?: > eval line \d+)* > eval:\d+:\d+/g, ":$1")), -1 === line.indexOf("@") && -1 === line.indexOf(":"))
      return new StackFrame({ functionName: line });
    var functionNameRegex = /((.*".+"[^@]*)?[^@]*)(?:@)/, matches = line.match(functionNameRegex), functionName = matches && matches[1] ? matches[1] : void 0, locationParts = this.extractLocation(line.replace(functionNameRegex, ""));
    return new StackFrame({ functionName, fileName: locationParts[0], lineNumber: locationParts[1], columnNumber: locationParts[2], source: line });
  }, this);
}, parseOpera: function(e) {
  return !e.stacktrace || e.message.indexOf("\n") > -1 && e.message.split("\n").length > e.stacktrace.split("\n").length ? this.parseOpera9(e) : e.stack ? this.parseOpera11(e) : this.parseOpera10(e);
}, parseOpera9: function(e) {
  for (var lineRE = /Line (\d+).*script (?:in )?(\S+)/i, lines = e.message.split("\n"), result = [], i = 2, len = lines.length; i < len; i += 2) {
    var match = lineRE.exec(lines[i]);
    match && result.push(new StackFrame({ fileName: match[2], lineNumber: match[1], source: lines[i] }));
  }
  return result;
}, parseOpera10: function(e) {
  for (var lineRE = /Line (\d+).*script (?:in )?(\S+)(?:: In function (\S+))?$/i, lines = e.stacktrace.split("\n"), result = [], i = 0, len = lines.length; i < len; i += 2) {
    var match = lineRE.exec(lines[i]);
    match && result.push(new StackFrame({ functionName: match[3] || void 0, fileName: match[2], lineNumber: match[1], source: lines[i] }));
  }
  return result;
}, parseOpera11: function(error) {
  return error.stack.split("\n").filter(function(line) {
    return !!line.match(FIREFOX_SAFARI_STACK_REGEXP) && !line.match(/^Error created at/);
  }, this).map(function(line) {
    var argsRaw, tokens = line.split("@"), locationParts = this.extractLocation(tokens.pop()), functionCall = tokens.shift() || "", functionName = functionCall.replace(/<anonymous function(: (\w+))?>/, "$2").replace(/\([^)]*\)/g, "") || void 0;
    functionCall.match(/\(([^)]*)\)/) && (argsRaw = functionCall.replace(/^[^(]+\(([^)]*)\)$/, "$1"));
    var args = void 0 === argsRaw || "[arguments not available]" === argsRaw ? void 0 : argsRaw.split(",");
    return new StackFrame({ functionName, args, fileName: locationParts[0], lineNumber: locationParts[1], columnNumber: locationParts[2], source: line });
  }, this);
} });
var IN_NODE = "undefined" != typeof process && process.release && "node" === process.release.name && void 0 === process.browser;
var nodeUrlMod;
var nodeFetch;
var nodePath;
var nodeVmMod;
var nodeFsPromisesMod;
var resolvePath;
var pathSep;
var loadBinaryFile;
var loadScript;
if (resolvePath = IN_NODE ? function(path, base) {
  return nodePath.resolve(base || ".", path);
} : function(path, base) {
  return void 0 === base && (base = location), new URL(path, base).toString();
}, IN_NODE || (pathSep = "/"), loadBinaryFile = IN_NODE ? async function(path, _file_sub_resource_hash) {
  if (path.startsWith("file://") && (path = path.slice("file://".length)), path.includes("://")) {
    let response = await nodeFetch(path);
    if (!response.ok)
      throw new Error(`Failed to load '${path}': request failed.`);
    return new Uint8Array(await response.arrayBuffer());
  }
  {
    const data = await nodeFsPromisesMod.readFile(path);
    return new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
  }
} : async function(path, subResourceHash) {
  const url = new URL(path, location);
  let options = subResourceHash ? { integrity: subResourceHash } : {}, response = await fetch(url, options);
  if (!response.ok)
    throw new Error(`Failed to load '${url}': request failed.`);
  return new Uint8Array(await response.arrayBuffer());
}, globalThis.document)
  loadScript = async (url) => await import(url);
else if (globalThis.importScripts)
  loadScript = async (url) => {
    try {
      globalThis.importScripts(url);
    } catch (e) {
      if (!(e instanceof TypeError))
        throw e;
      await import(url);
    }
  };
else {
  if (!IN_NODE)
    throw new Error("Cannot determine runtime environment");
  loadScript = async function(url) {
    url.startsWith("file://") && (url = url.slice("file://".length));
    url.includes("://") ? nodeVmMod.runInThisContext(await (await nodeFetch(url)).text()) : await import(nodeUrlMod.pathToFileURL(url).href);
  };
}
function setStandardStreams(Module, stdin, stdout, stderr) {
  stdout && (Module.print = stdout), stderr && (Module.printErr = stderr), stdin && Module.preRun.push(function() {
    Module.FS.init(function(stdin2) {
      const encoder = new TextEncoder();
      let input = new Uint8Array(0), inputIndex = -1;
      function stdinWrapper() {
        try {
          if (-1 === inputIndex) {
            let text = stdin2();
            if (null == text)
              return null;
            if ("string" != typeof text)
              throw new TypeError(`Expected stdin to return string, null, or undefined, got type ${typeof text}.`);
            text.endsWith("\n") || (text += "\n"), input = encoder.encode(text), inputIndex = 0;
          }
          if (inputIndex < input.length) {
            let character = input[inputIndex];
            return inputIndex++, character;
          }
          return inputIndex = -1, null;
        } catch (e) {
          throw console.error("Error thrown in stdin:"), console.error(e), e;
        }
      }
      return stdinWrapper;
    }(stdin), null, null);
  });
}
function finalizeBootstrap(API, config) {
  API.runPythonInternal_dict = API._pyodide._base.eval_code("{}"), API.importlib = API.runPythonInternal("import importlib; importlib");
  let import_module = API.importlib.import_module;
  API.sys = import_module("sys"), API.sys.path.insert(0, config.homedir);
  let globals = API.runPythonInternal("import __main__; __main__.__dict__"), builtins = API.runPythonInternal("import builtins; builtins.__dict__");
  var builtins_dict;
  API.globals = (builtins_dict = builtins, new Proxy(globals, { get: (target, symbol) => "get" === symbol ? (key) => {
    let result = target.get(key);
    return void 0 === result && (result = builtins_dict.get(key)), result;
  } : "has" === symbol ? (key) => target.has(key) || builtins_dict.has(key) : Reflect.get(target, symbol) }));
  let importhook = API._pyodide._importhook;
  importhook.register_js_finder(), importhook.register_js_module("js", config.jsglobals), importhook.register_unvendored_stdlib_finder();
  let pyodide2 = API.makePublicAPI();
  return importhook.register_js_module("pyodide_js", pyodide2), API.pyodide_py = import_module("pyodide"), API.pyodide_code = import_module("pyodide.code"), API.pyodide_ffi = import_module("pyodide.ffi"), API.package_loader = import_module("pyodide._package_loader"), pyodide2.pyodide_py = API.pyodide_py, pyodide2.globals = API.globals, pyodide2;
}
async function loadPyodide(options = {}) {
  await async function() {
    if (!IN_NODE)
      return;
    if (nodeUrlMod = (await import("url")).default, nodeFsPromisesMod = await import("fs/promises"), nodeFetch = globalThis.fetch ? fetch : (await import("node-fetch")).default, nodeVmMod = (await import("vm")).default, nodePath = await import("path"), pathSep = nodePath.sep, "undefined" != typeof __require)
      return;
    const node_modules = { fs: await import("fs"), crypto: await import("crypto"), ws: await Promise.resolve().then(() => __toESM(require_browser())), child_process: await import("child_process") };
    globalThis.require = function(mod) {
      return node_modules[mod];
    };
  }();
  let indexURL = options.indexURL || function() {
    if ("string" == typeof __dirname)
      return __dirname;
    let err;
    try {
      throw new Error();
    } catch (e) {
      err = e;
    }
    let fileName = ErrorStackParser.parse(err)[0].fileName;
    const indexOfLastSlash = fileName.lastIndexOf(pathSep);
    if (-1 === indexOfLastSlash)
      throw new Error("Could not extract indexURL path from pyodide module location");
    return fileName.slice(0, indexOfLastSlash);
  }();
  indexURL = resolvePath(indexURL), indexURL.endsWith("/") || (indexURL += "/"), options.indexURL = indexURL;
  const default_config = { fullStdLib: true, jsglobals: globalThis, stdin: globalThis.prompt ? globalThis.prompt : void 0, homedir: "/home/pyodide", lockFileURL: indexURL + "repodata.json" }, config = Object.assign(default_config, options), pyodide_py_tar_promise = loadBinaryFile(config.indexURL + "pyodide_py.tar"), Module = { noImageDecoding: true, noAudioDecoding: true, noWasmDecoding: false, preloadedWasm: {}, preRun: [] }, API = { config };
  Module.API = API, setStandardStreams(Module, config.stdin, config.stdout, config.stderr), function(Module2, path) {
    Module2.preRun.push(function() {
      try {
        Module2.FS.mkdirTree(path);
      } catch (e) {
        console.error(`Error occurred while making a home directory '${path}':`), console.error(e), console.error("Using '/' for a home directory instead"), path = "/";
      }
      Module2.ENV.HOME = path, Module2.FS.chdir(path);
    });
  }(Module, config.homedir);
  const moduleLoaded = new Promise((r) => Module.postRun = r);
  Module.locateFile = (path) => config.indexURL + path;
  const scriptSrc = `${config.indexURL}pyodide.asm.js`;
  if (await loadScript(scriptSrc), await _createPyodideModule(Module), await moduleLoaded, "0.21.3" !== API.version)
    throw new Error(`Pyodide version does not match: '0.21.3' <==> '${API.version}'. If you updated the Pyodide version, make sure you also updated the 'indexURL' parameter passed to loadPyodide.`);
  Module.locateFile = (path) => {
    throw new Error("Didn't expect to load any more file_packager files!");
  };
  const pyodide_py_tar = await pyodide_py_tar_promise;
  !function(Module2, pyodide_py_tar2) {
    let stream = Module2.FS.open("/pyodide_py.tar", "w");
    Module2.FS.write(stream, pyodide_py_tar2, 0, pyodide_py_tar2.byteLength, void 0, true), Module2.FS.close(stream);
    const code_ptr = Module2.stringToNewUTF8('\nfrom sys import version_info\npyversion = f"python{version_info.major}.{version_info.minor}"\nimport shutil\nshutil.unpack_archive("/pyodide_py.tar", f"/lib/{pyversion}/site-packages/")\ndel shutil\nimport importlib\nimportlib.invalidate_caches()\ndel importlib\n    ');
    if (Module2._PyRun_SimpleString(code_ptr))
      throw new Error("OOPS!");
    Module2._free(code_ptr), Module2.FS.unlink("/pyodide_py.tar");
  }(Module, pyodide_py_tar), Module._pyodide_init();
  const pyodide2 = finalizeBootstrap(API, config);
  if (pyodide2.version.includes("dev") || API.setCdnUrl(`https://cdn.jsdelivr.net/pyodide/v${pyodide2.version}/full/`), await API.packageIndexReady, "0.21.3" !== API.repodata_info.version)
    throw new Error("Lock file version doesn't match Pyodide version");
  return config.fullStdLib && await pyodide2.loadPackage(["distutils"]), pyodide2.runPython("print('Python initialization complete')"), pyodide2;
}

// src/pyodide-proxy.ts
async function setupPythonEnv(pyodide2, callJS2) {
  const repr = pyodide2.globals.get("repr");
  pyodide2.globals.set("js_pyodide", pyodide2);
  const pyconsole = await pyodide2.runPythonAsync(`
  import pyodide.console
  import __main__
  pyodide.console.PyodideConsole(__main__.__dict__)
  `);
  const tabComplete = pyconsole.complete.copy();
  pyconsole.destroy();
  if (callJS2) {
    pyodide2.globals.set("callJS", callJS2);
  }
  const shortFormatLastTraceback = await pyodide2.runPythonAsync(`
  def _short_format_last_traceback() -> str:
      import sys
      import traceback
      e = sys.last_value
      found_marker = False
      nframes = 0
      for (frame, _) in traceback.walk_tb(e.__traceback__):
          if frame.f_code.co_filename in ("<console>", "<exec>"):
              found_marker = True
          if found_marker:
              nframes += 1
      return "".join(traceback.format_exception(type(e), e, e.__traceback__, -nframes))

  _short_format_last_traceback
  `);
  await pyodide2.runPythonAsync(`del _short_format_last_traceback`);
  return {
    repr,
    tabComplete,
    shortFormatLastTraceback
  };
}
function processReturnValue(value, returnResult = "none", pyodide2, repr) {
  const possibleReturnValues = {
    get value() {
      if (pyodide2.isPyProxy(value)) {
        return value.toJs();
      } else {
        return value;
      }
    },
    get printed_value() {
      return repr(value);
    },
    get to_html() {
      let toHtml;
      try {
        toHtml = pyodide2.globals.get("_to_html");
      } catch (e) {
        console.error("Couldn't find _to_html function: ", e);
        toHtml = (x) => ({
          type: "text",
          value: "Couldn't finding _to_html function."
        });
      }
      const val = toHtml(value).toJs({
        dict_converter: Object.fromEntries
      });
      return val;
    },
    get none() {
      return void 0;
    }
  };
  return possibleReturnValues[returnResult];
}

// src/pyodide-worker.ts
var pyodideStatus = "none";
var pyodide;
self.stdout_callback = function(s) {
  self.postMessage({ type: "nonreply", subtype: "output", stdout: s });
};
self.stderr_callback = function(s) {
  self.postMessage({ type: "nonreply", subtype: "output", stderr: s });
};
async function callJS(fnName, args) {
  self.postMessage({
    type: "nonreply",
    subtype: "callJS",
    fnName: fnName.toJs(),
    args: args.toJs()
  });
}
var pyUtils;
self.onmessage = async function(e) {
  const msg = e.data;
  if (msg.type === "openChannel") {
    const clientPort = e.ports[0];
    openChannel(msg.path, msg.appName, clientPort, pyodide);
    return;
  } else if (msg.type === "makeRequest") {
    const clientPort = e.ports[0];
    makeRequest(msg.scope, msg.appName, clientPort, pyodide);
    return;
  }
  const messagePort = e.ports[0];
  try {
    if (msg.type === "init") {
      if (pyodideStatus === "none") {
        pyodideStatus = "loading";
        pyodide = await loadPyodide({
          ...msg.config,
          stdout: self.stdout_callback,
          stderr: self.stderr_callback
        });
        pyUtils = await setupPythonEnv(pyodide, callJS);
        pyodideStatus = "loaded";
      }
      messagePort.postMessage({ type: "reply", subtype: "done" });
    } else if (msg.type === "loadPackagesFromImports") {
      await pyodide.loadPackagesFromImports(msg.code);
    } else if (msg.type === "runPythonAsync") {
      await pyodide.loadPackagesFromImports(msg.code);
      const result = await pyodide.runPythonAsync(
        msg.code
      );
      if (msg.printResult && result !== void 0) {
        self.stdout_callback(pyUtils.repr(result));
      }
      try {
        const processedResult = processReturnValue(
          result,
          msg.returnResult,
          pyodide,
          pyUtils.repr
        );
        messagePort.postMessage({
          type: "reply",
          subtype: "done",
          value: processedResult
        });
      } finally {
        if (pyodide.isPyProxy(result)) {
          result.destroy();
        }
      }
    } else if (msg.type === "tabComplete") {
      const completions = pyUtils.tabComplete(msg.code).toJs()[0];
      messagePort.postMessage({
        type: "reply",
        subtype: "tabCompletions",
        completions
      });
    } else if (msg.type === "callPyAsync") {
      const { fnName, args, kwargs } = msg;
      let fn = pyodide.globals.get(fnName[0]);
      for (const el of fnName.slice(1)) {
        fn = fn[el];
      }
      const resultMaybePromise = fn.callKwargs(...args, kwargs);
      const result = await Promise.resolve(resultMaybePromise);
      if (msg.printResult && result !== void 0) {
        self.stdout_callback(pyUtils.repr(result));
      }
      try {
        const processedResult = processReturnValue(
          result,
          msg.returnResult,
          pyodide,
          pyUtils.repr
        );
        messagePort.postMessage({
          type: "reply",
          subtype: "done",
          value: processedResult
        });
      } finally {
        if (pyodide.isPyProxy(result)) {
          result.destroy();
        }
      }
    } else {
      messagePort.postMessage({
        type: "reply",
        subtype: "done",
        error: new Error(`Unknown message type: ${msg.toString()}`)
      });
    }
  } catch (e2) {
    if (e2 instanceof pyodide.PythonError) {
      e2.message = pyUtils.shortFormatLastTraceback();
    }
    messagePort.postMessage({
      type: "reply",
      subtype: "done",
      error: errorToPostableErrorObject(e2)
    });
  }
};
