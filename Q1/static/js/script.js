function draw_slider(column, min, max, step){
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
  // Dictionary to hold all filter values
  const filterValues = {};

  // Start and End Times
  filterValues['startTime'] = document.getElementById("start-time").value;
  filterValues['endTime'] = document.getElementById("end-time").value;

  // Word list
  const wordListItems = document.querySelectorAll("#wordList li");
  filterValues['keywords'] = Array.from(wordListItems).map(item => item.textContent.trim());

  // Selected authors
  const authorCheckboxes = document.querySelectorAll("#checkboxes input[type=checkbox]:checked");
  filterValues['authors'] = Array.from(authorCheckboxes).map(cb => cb.id);

  // Emergency slider value (example assumes you're using noUiSlider)
  const slider = document.getElementById('emergency-time-slider');
  if (slider.noUiSlider) {
      filterValues['emergencyMinutes'] = slider.noUiSlider.get(); // Might return a string or array depending on config
  } else {
      filterValues['emergencyMinutes'] = null;
  }

  console.log(filterValues);
  return filterValues;
}

function update(){
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
})
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

  update()
}