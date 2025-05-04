function draw_slider(column, min, max, step) {
  slider = document.getElementById(column+'-slider')
  noUiSlider.create(slider, {
    start: [min, max],
    connect: false,
        tooltips: true,
    step: step,
    range: {'min': min, 'max': max}
  });
}

function getFilterValues() {
  const filterValues = {};

  // Start and End Times
  const startTimeSelect = document.getElementById("start-time");
  const endTimeSelect = document.getElementById("end-time");

  const startTime = startTimeSelect.value;
  const endTime = endTimeSelect.value;

  const defaultStartTime = startTimeSelect.options[0].value;
  const defaultEndTime = endTimeSelect.options[endTimeSelect.options.length - 1].value;

  if ((startTime !== defaultStartTime) || (endTime !== defaultEndTime)) {
    filterValues['startTime'] = startTime;
    filterValues['endTime'] = endTime;
  }

  // Keywords
  const wordListItems = document.querySelectorAll("#wordList li");
  const keywords = Array.from(wordListItems).map(item => item.textContent.trim());
  if (keywords.length > 0) {
    filterValues['keywords'] = keywords;
  }

  // Selected authors
  const authorCheckboxes = document.querySelectorAll("#checkboxes input[type=checkbox]:checked");
  const selectedAuthors = Array.from(authorCheckboxes).map(cb => cb.id);
  if (selectedAuthors.length > 0) {
    filterValues['authors'] = selectedAuthors;
  }

  // Emergency slider value
  const slider = document.getElementById('emergency-time-slider');
  if (slider.noUiSlider) {
    const emergencyRange = slider.noUiSlider.get().map(val => parseFloat(val));
    const defaultRange = [0, 10];

    if (emergencyRange[0] !== defaultRange[0] || emergencyRange[1] !== defaultRange[1]) {
      filterValues['emergencyMinutes'] = emergencyRange;
    }
  }

  console.log(filterValues);
  return filterValues;
}

function update() {
  // Notify that applying filters
  document.getElementById('messages-list').innerHTML = "Applying filters...";
  document.getElementById('ai-summary-text').innerHTML = "Generating summary...";

  // Get values of all filters
  const filterData = getFilterValues();
  // Send to python
  fetch('/update', {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify(filterData),
    cache: 'no-cache',
    headers: new Headers({
        'content-type': 'application/json'
    })
}).then(async function(response){
    var results = JSON.parse(JSON.stringify((await response.json())))

    // Update display with results
    document.getElementById('messages-list').innerHTML = results.df;
    document.getElementById('ai-summary-text').innerHTML = results.summary;

    // Update the chart
    refreshChartData(); 
})
}

function refreshChartData() {
  console.log(messageChart)
  fetch('/chart-data')
    .then(response => response.json())
    .then(data => {
      messageChart.data.labels = data.labels;
      messageChart.data.datasets[0].data = data.data;
      messageChart.data.datasets[0].backgroundColor = data.colors;
      messageChart.data.datasets[0].borderColor = data.colors;
      messageChart.update();
    });
}


function resetFilters() {
  // Reset start and end time select dropdowns to their default values
  document.getElementById("start-time").selectedIndex = 0;
  document.getElementById("end-time").selectedIndex = document.getElementById("end-time").options.length - 1;

  // Reset the emergency slider 
  var slider = document.getElementById('emergency-time-slider');
  slider.noUiSlider.set([0, 10]);

  // Clear keyword list
  const wordList = document.getElementById('wordList');
  wordList.innerHTML = ''; // Clear the list

  // Clear word input field
  const wordInput = document.getElementById('wordInput');
  wordInput.value = '';

  // Deselect all author checkboxes
  const checkboxes = document.querySelectorAll("#checkboxes input[type='checkbox']");
  checkboxes.forEach(cb => cb.checked = false);

  // Clear selected authors display
  document.getElementById('selected-authors-list').innerHTML = '';

  // Reset display
  update();
}

// Preset filters
function preset_filter(mode) {
  // Select preset
  preset = presets[mode]

  // Set start time
  const startSelect = document.getElementById("start-time");
  if (preset.startTime) {
    for (let i = 0; i < startSelect.options.length; i++) {
      if (startSelect.options[i].value === preset.startTime) {
        startSelect.selectedIndex = i;
        break;
      }
    }
  } else {
    startSelect.selectedIndex = 0;
  }

  // Set end time
  const endSelect = document.getElementById("end-time");
  if (preset.endTime) {
    for (let i = 0; i < endSelect.options.length; i++) {
      if (endSelect.options[i].value === preset.endTime) {
        endSelect.selectedIndex = i;
        break;
      }
    }
  } else {
    endSelect.selectedIndex = endSelect.options.length - 1;
  }

  // Set emergency slider
  const slider = document.getElementById('emergency-time-slider');
  if (preset.emergencyMinutes && preset.emergencyMinutes.length === 2) {
    slider.noUiSlider.set(preset.emergencyMinutes);
  } else {
    slider.noUiSlider.set([0, 10]);
  }

  // Set keywords
  words.length = 0;
  const wordList = document.getElementById('wordList');
  wordList.innerHTML = '';
  if (preset.keywords && preset.keywords.length > 0) {
    preset.keywords.forEach(kw => {
      words.push(kw);
      const li = document.createElement('li');
      li.textContent = kw;
      wordList.appendChild(li);
    });
  }

  // Set authors
  const checkboxes = document.querySelectorAll("#checkboxes input[type='checkbox']");
  const selectedAuthors = preset.authors || [];

  checkboxes.forEach(cb => {
    cb.checked = selectedAuthors.includes(cb.id);
  });

  const selectedAuthorsList = document.getElementById('selected-authors-list');
  selectedAuthorsList.innerHTML = selectedAuthors.map(author => `<li>${author}</li>`).join('');

  update();
}