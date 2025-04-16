function draw_slider(column, min, max, step){
  slider = document.getElementById(column+'-slider')
  noUiSlider.create(slider, {
    start: [min, max],
    connect: false,
        tooltips: true,
    step: step,
    range: {'min': min, 'max': max}
  });
  // slider.noUiSlider.on('change', function(){
  //     update(scatter1_svg, scatter2_svg, scatter1_scale, scatter2_scale)
  // });
}

function update(){
  
}