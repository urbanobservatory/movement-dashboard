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
  
  setInterval(
    function () {
	  if (activeDocumentId) {
	    loadDocumentById(activeDocumentId);	
	  }
	},
	60 * 1000
  );
});

function loadOptions() {
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
  if (!document) return;
  
  activeDocumentId = id;
  window.location = '#' + id;
  
  console.log('Loading document from', document.path);
  loadDocument(document.path, document.type);
  documentSelector.selectedIndex = documentIndex;
}

function loadDocument(path, type) {
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
