




function createSVGPlot(SVG_WIDTH, SVG_HEIGHT, X_LEFT_OFFSET, X_RIGHT_OFFSET, 
                       Y_TOP_OFFSET, Y_BOTTOM_OFFSET, DATA_DOMAIN, HTML_ID) {
  const svg = d3.select(HTML_ID)
  .append("svg")
  .attr("width", SVG_WIDTH)
  .attr("height", SVG_HEIGHT)
  .style("overflow", "visible");
  
  console.log([SVG_WIDTH, SVG_HEIGHT, X_LEFT_OFFSET, X_RIGHT_OFFSET, 
    Y_TOP_OFFSET, Y_BOTTOM_OFFSET, DATA_DOMAIN, HTML_ID])

  const xScale = d3.scaleTime().range([X_LEFT_OFFSET, SVG_WIDTH-X_RIGHT_OFFSET]);
  const yScale = d3.scaleLinear().range([SVG_HEIGHT-Y_TOP_OFFSET, Y_BOTTOM_OFFSET]).domain(DATA_DOMAIN);
  return [svg, xScale, yScale]
}

function setupLineScatter(svg, id, xScale, yScale, SMOOTHING) {
  const g = svg.append("g")
    .attr("class", `${id}-plot`);

  g.append("g")
    .attr("class", `${id}-plot-scatter`)

  const scatterGroup = svg.append("g")
    .attr("class", "dots-group");

  const path = g.append("path")
    .attr("class", "line")
    .attr("fill", "none")
    .attr("stroke", "steelblue");
  
  const d3line = d3.line()
    .x(d => xScale(d.t))
    .y(d => yScale(d.value))
  if (SMOOTHING) {
    d3line.curve(d3.curveMonotoneX);
  }
  return [path, d3line, scatterGroup]
}

function appendSVGAxis(svg, id, SVG_WIDTH, SVG_HEIGHT, Y_LABEL, X_LABEL) {
    
  svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0, ${SVG_HEIGHT-Y_BOTTOM_OFFSET})`);
    
  svg.append("g")
    .attr("class", "y-axis")


    // y label
  svg.append("text")
  .attr("class", "svg-text")
    .attr("transform", "rotate(-90)")
    .attr("y", -50)
    .attr("x", -SVG_HEIGHT/2)
    .attr("dy", "1em")
    .style("text-anchor", "middle")
    .text(Y_LABEL); // Replace with your desired label text
    // x label
  svg.append("text")
    .attr("y", SVG_HEIGHT+15)
    .attr("x", SVG_WIDTH/2)
    .attr("dy", "1em")
    .style("text-anchor", "middle")
    .text(X_LABEL); // Replace with your desired label text
}


function initOnePlot(SVG_WIDTH, SVG_HEIGHT, X_LEFT_OFFSET, X_RIGHT_OFFSET, 
                     Y_TOP_OFFSET, Y_BOTTOM_OFFSET, DATA_DOMAIN, HTML_ID, NAME, 
                     SMOOTHING, N_Y_TICKS, Y_LABEL, X_LABEL) {
  const [svg, xScale, yScale] = createSVGPlot(SVG_WIDTH, SVG_HEIGHT, X_LEFT_OFFSET, 
                                              X_RIGHT_OFFSET, Y_TOP_OFFSET, 
                                              Y_BOTTOM_OFFSET, DATA_DOMAIN, HTML_ID)
  const [path, d3line, scatterGroup] = setupLineScatter(svg, NAME, 
                                                        xScale, yScale,
                                                        SMOOTHING);
  appendSVGAxis(svg, NAME, SVG_WIDTH, SVG_HEIGHT, Y_LABEL, X_LABEL)
  yScaleSetter(svg, yScale, DATA_DOMAIN, N_Y_TICKS)

  svg.selectAll("text") // Select all text elements within the SVG
   .style("font-family", "Futura, Arial, sans-serif") // Set the desired font family
   .style("fill", "#444444"); // Set the font color


  return [svg, xScale, yScale, path, d3line, scatterGroup]
}


function yScaleSetter(svg, yScale, domain, N_Y_TICKS) {
  yScale.domain(domain);
  svg.select(".y-axis").call(d3.axisLeft(yScale).ticks(N_Y_TICKS));
  svg.select(".y-axis").selectAll("path")
    .style("stroke", "#444444")
  svg.select(".y-axis").selectAll(".ticks")
    .style("stroke", "#444444")

}


function xScaleSetter(svg, xScale, domain) {
  xScale.domain(domain);
  svg.select(".x-axis").call(d3.axisBottom(xScale).ticks(5).tickFormat(d3.timeFormat("%S")));
  svg.select(".x-axis").selectAll("path")
    .style("stroke", "#444444")
  svg.select(".x-axis").selectAll(".ticks")
    .style("stroke", "#444444")
}


function redrawScatter(scatterGroup, distData, xScale, yScale) {
  const dots = scatterGroup
    .selectAll(".dot")
    .data(distData);
 
  dots.exit().remove();
  dots.enter()
    .append("circle")
    .attr("class", "dot")
    .attr("r", 2)
    .attr("fill", "steelblue")
    .merge(dots)
    .attr("cx", d => xScale(d.t))
    .attr("cy", d => yScale(d.value));
  
  
//   const dots = scatterGroup
//   .selectAll("line.dot") // Select lines with the "dot" class
//   .data(distData);

// dots.exit().remove();

// const enteringDots = dots.enter()
//   .append("line") // Use "line" instead of "circle"
//   .attr("class", "dot") // You can keep this line if you want to style the lines differently from other lines
//   .attr("x1", d => xScale(d.t))
//   .attr("x2", d => xScale(d.t))
//   .attr("y1", 20)
//   .attr("y2", 0)
//   .attr("stroke", "steelblue")
//   .attr("stroke-width", 2);

// enteringDots.transition()
//   .duration(300)
//   .attr("y2", d => yScale(d.value));

    
}

function updateOnePlot(toT, fromT, distData, plotRef, SHOW_SCATTER, SHOW_LINE) {
  const [svg, xScale, yScale, path, d3line, scatterGroup] = plotRef;
  xScaleSetter(svg, xScale, [fromT, toT])

  if (SHOW_LINE) {
    path.datum(distData)
     .attr("d", d3line);
  }
  if (SHOW_SCATTER) {
    redrawScatter(scatterGroup, distData, xScale, yScale)
  }
}

function updatePlots(toT, fromT, data) {
  for (let i = 0; i < PLOT_NAMES.length; i++) {
    const plotData = data.filter(sensorReading => sensorReading.id == PLOT_NAMES[i])
    console.debug("plotData: ", plotData)
    updateOnePlot(toT, fromT, plotData, plotRefs[i], PLOT_SHOW_SCATTERS[i], PLOT_SHOW_LINES[i])
  }
}

function initPlots() {
  const plotRefs = []
  for (let i = 0; i < PLOT_NAMES.length; i++) {
    plotRefs.push(initOnePlot(SVG_WIDTH, PLOT_SVG_HEIGHTS[i], X_LEFT_OFFSET, 
                              X_RIGHT_OFFSET, Y_TOP_OFFSET, 
                              Y_BOTTOM_OFFSET, PLOT_DATA_DOMAINS[i], 
                              PLOT_HTML_IDS[i], PLOT_NAMES[i], 
                              PLOT_SMOOTHINGS[i], PLOT_N_Y_TICKS[i],
                              PLOT_Y_LABELS[i], PLOT_X_LABELS[i]))
  }
  return plotRefs
}

function setupWebsocket(url) {
  var ws = new WebSocket(url);
  ws.onmessage = function(messageEvent) {
    let newData = JSON.parse(messageEvent.data);
    console.debug("WS: ", newData)
    DATA_BUFFER.push(newData);
  };
  return ws
}

async function updateLoop(ws) {
  let data = [];
  while (true) {
    if (DATA_BUFFER.length > 0) {
      console.debug("=======processData========")
      
      let toT = DATA_BUFFER[DATA_BUFFER.length - 1].t
      let fromT = toT - TIMELINE_INTERVAL * 1000 // in seconds
      console.debug("data length", data.length)
      data.push(...DATA_BUFFER)
      console.debug("buffer length", DATA_BUFFER.length)
      console.debug("data length", data.length)
      DATA_BUFFER = []
      data = data.filter(sensorReading => sensorReading.t > fromT)
      
      console.debug("=======updateChart========")
      updatePlots(toT, fromT, data);
    }
    await new Promise(resolve => setTimeout(resolve, 33)); // Wait 33ms
  }
}




const SVG_WIDTH = 800;
const X_LEFT_OFFSET = 10;
const X_RIGHT_OFFSET = 10;
const Y_TOP_OFFSET = 10;
const Y_BOTTOM_OFFSET = 10;
const TIMELINE_INTERVAL = 5.; // in seconds

const PLOT_NAMES = ["distanceSensorLeft", "reward", "lickSensor", "photoResistor"]
const PLOT_HTML_IDS = ["#distance-sensor-chart-container","#reward-chart-container",
                     "#lick-sensor-chart-container","#photoresisitor-sensor-chart-container"]
const PLOT_DATA_DOMAINS = [[-5, 90],[-.1, 1.1],[-.1, 1.1], [-.1, 1.1]];
const PLOT_SVG_HEIGHTS = [300, 50, 50, 50 ];

const PLOT_N_Y_TICKS = [5, 1, 1, 1];
const PLOT_Y_LABELS = ["Distance Sensor [cm]", "Reward", "Lick", "Photores."];
const PLOT_X_LABELS = ["", "", "", "Timestamp [sec]"];

const PLOT_SHOW_SCATTERS = [true, true, true, true];
const PLOT_SHOW_LINES = [true, false, false, true];
const PLOT_SMOOTHINGS = [true, false, false, false];

const WEBSOCKET_URL = "ws://localhost:8000/ws"
let DATA_BUFFER = [];

// ------------------------ //

const plotRefs = initPlots()

websocket = setupWebsocket(WEBSOCKET_URL)
updateLoop(websocket);




















