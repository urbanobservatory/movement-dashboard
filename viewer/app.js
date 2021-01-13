var contentArea = null;
var documentSelector = null;
var documentList = null;
var activeDocumentId = null;

window.addEventListener('load', function () {
  console.log('Loaded.');
  contentArea = document.getElementById('content-area');
  documentSelector = document.getElementById('document-selector');
  loadOptions();
  
  documentSelector.addEventListener('change', function (e) {
    var options = e.target.options;
	var selectedOption = options[e.target.selectedIndex];
	console.log('Document selection changed to', selectedOption.id);
	loadDocumentById(selectedOption.id);
  });
  
  /* setInterval(
    function () {
	  if (activeDocumentId) {
	    loadDocumentById(activeDocumentId);	
	  }
	},
	60 * 1000
  ); */
});

function loadOptions() {
  loadingSpinner();
  fetch('documents.json')
    .then(
	  function (response) {
		  return response.json();
	  }
    )
	.then(
	  function (documents) {
		documentList = documents;
		  
        for (var i = documentSelector.options.length - 1; i >= 0; i--) {
          documentSelector.options[i] = null;
        }
		for (var i = 0; i < documents.length; i++) {
          var newOption = document.createElement('option');
		  if (documents[i].coverage === 'national') {
			  newOption.className = 'coverage-national';
		  }
          newOption.innerText = documents[i].title;
          newOption.id = documents[i].id;
          documentSelector.appendChild(newOption);
		}
		
		if (window.location.hash) {
          loadDocumentById(window.location.hash.substr(1));
		} else {
          loadDocumentById(documents[0].id);
		}
	  }
	);
}

function loadDocumentById(id) {
  var documentIndex = documentList.findIndex(
	function(d) {
	  return d.id === id;
	}
  );
  var document = documentList[documentIndex];
  if (!document) {
	  document = documentList[0];
  }
  
  activeDocumentId = id;
  window.location = '#' + id;
  
  console.log('Loading document from', document.path);
  loadDocument(document.path, document.type);
  documentSelector.selectedIndex = documentIndex;
}

function loadingSpinner() {
	contentArea.innerHTML = '<div class="spinner"><div class="lds-roller"><div></div><div></div><div></div><div></div><div></div><div></div><div></div><div></div></div></div>';
}

function loadDocument(path, type) {
  loadingSpinner();
  fetch(path)
    .then(
	  function (response) {
		  return response.text();
	  }
    )
	.then(
	  function (html) {
		  if (!contentArea) return;
		  contentArea.innerHTML = html;
	  }
	)
    .catch(
	  function (e) {
		  contentArea.innerHTML = '<h1>Sorry, an error occured.</h1>';
		  contentArea.innerHTML += e.message;
		  contentArea.innerHTML += '<pre>' + e.stack + '</pre>';
	  }
	)
}

/**
 No real code below. Polyfills only...
*/
// https://tc39.github.io/ecma262/#sec-array.prototype.findindex
if (!Array.prototype.findIndex) {
  Object.defineProperty(Array.prototype, 'findIndex', {
    value: function(predicate) {
     // 1. Let O be ? ToObject(this value).
      if (this == null) {
        throw new TypeError('"this" is null or not defined');
      }

      var o = Object(this);

      // 2. Let len be ? ToLength(? Get(O, "length")).
      var len = o.length >>> 0;

      // 3. If IsCallable(predicate) is false, throw a TypeError exception.
      if (typeof predicate !== 'function') {
        throw new TypeError('predicate must be a function');
      }

      // 4. If thisArg was supplied, let T be thisArg; else let T be undefined.
      var thisArg = arguments[1];

      // 5. Let k be 0.
      var k = 0;

      // 6. Repeat, while k < len
      while (k < len) {
        // a. Let Pk be ! ToString(k).
        // b. Let kValue be ? Get(O, Pk).
        // c. Let testResult be ToBoolean(? Call(predicate, T, « kValue, k, O »)).
        // d. If testResult is true, return k.
        var kValue = o[k];
        if (predicate.call(thisArg, kValue, k, o)) {
          return k;
        }
        // e. Increase k by 1.
        k++;
      }

      // 7. Return -1.
      return -1;
    },
    configurable: true,
    writable: true
  });
}

