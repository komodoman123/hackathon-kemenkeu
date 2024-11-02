import React, { useState, useEffect, useRef } from 'react';
import { Send, Plus, Loader2 } from 'lucide-react';
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { ScrollArea } from "../components/ui/scroll-area";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement, ArcElement } from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';
import ReactMarkdown from 'react-markdown';


const LoadingMessage = () => (
  <div className="flex justify-start">
    <div className="max-w-[80%] rounded-xl p-3 shadow-sm bg-white border-2 border-gray-100">
      <div className="flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
        <span className="text-sm text-gray-500">Analyzing data...</span>
      </div>
    </div>
  </div>
);

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement, 
  Title,
  Tooltip,
  Legend
);

const ChatbotInterface = () => {
  const EXCLUDED_COLUMNS = [
    'filtered_keywords',
  ];
  const chatContainerRef = useRef(null);
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Hello! I can help you analyze your data. Type anything to start the analysis!' }
  ]);
  const [showVisualizations, setShowVisualizations] = useState(false);
  const [isExpanding, setIsExpanding] = useState(false);
  const [sessionId, setSessionId] = useState(Date.now().toString());
  const [rawData, setRawData] = useState(null);
  const [barData, setBarData] = useState(null);
  const [chartTitle, setChartTitle] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [chartsInfo, setChartsInfo] = useState([]);
  const messagesEndRef = useRef(null);

  const inputRef = useRef(null);
  const formatBotMessage = (message) => {
    const formattedMessage = message.replace(/(\d+\. \*\*.*?\*\*:) /g, '$1\n');
    return formattedMessage;
  };
  
  const BotMessage = ({ content }) => (
    <ReactMarkdown
      className="prose prose-sm max-w-none prose-p:my-1 prose-strong:text-blue-600"
      components={{
        p: ({ children }) => <p className="mb-2">{children}</p>,
        strong: ({ children }) => <strong className="font-semibold text-blue-600">{children}</strong>,
        li: ({ children }) => <li className="mb-2">{children}</li>,
      }}
    >
      {formatBotMessage(content)}
    </ReactMarkdown>
  );
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: "smooth",
        block: "end",
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const isNumeric = (value) => !isNaN(parseFloat(value)) && isFinite(value);

  const formatValue = (value, columnName) => {
    if (columnName === 'kode_rup') {
      return value;
    }
    
    if (isNumeric(value)) {
      if (value > 1000) {
        return `Rp ${Number(value).toLocaleString('id-ID')}`;
      }
      return value.toLocaleString('id-ID');
    }
    return value;
  };



const renderChart = (chart) => {
  const { chart_data, type, visualization } = chart;
  const { chart_title, x_column, y_column, y_columns, value_column, label_column } = visualization;

  const options = getChartOptions(type, chart_title);

  const labels = chart_data.map((item) => item[x_column]);
  let datasets;
  console.log("chart is ", type);
  switch (type) {
    case 'bar':
      datasets = [
        {
          label: y_column.replace(/_/g, ' '),
          data: chart_data.map((item) => item[y_column]),
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1,
        }
      ];
      return <Bar data={{ labels, datasets }} options={options} />;

    case 'line':
      datasets = [
        {
          label: y_columns ? y_columns[0].replace(/_/g, ' ') : y_column.replace(/_/g, ' '),
          data: chart_data.map((item) => item[y_columns ? y_columns[0] : y_column]),
          backgroundColor: 'rgba(153, 102, 255, 0.2)',
          borderColor: 'rgba(153, 102, 255, 1)',
          borderWidth: 1,
          fill: false
        }
      ];
      return <Line data={{ labels, datasets }} options={options} />;

      case 'histogram': {
        const dates = chart_data.map((item) => new Date(item[visualization.x_column])); 
        const minDate = new Date(Math.min(...dates));
        const maxDate = new Date(Math.max(...dates));
      

        const binSize = (maxDate - minDate) / visualization.bins;
        const binLabels = [];
        const binCounts = Array(visualization.bins).fill(0); 
      
       
        for (let i = 0; i < visualization.bins; i++) {
          const binStart = new Date(minDate.getTime() + i * binSize);
          binLabels.push(binStart.toLocaleDateString('id-ID', { month: 'short', year: 'numeric' }));
        }
      

        dates.forEach((date) => {
          const binIndex = Math.floor((date - minDate) / binSize);
          if (binIndex < visualization.bins) {
            binCounts[binIndex]++;
          }
        });
      
        datasets = [
          {
            label: 'Frequency',
            data: binCounts, 
            backgroundColor: 'rgba(153, 102, 255, 0.2)',
            borderColor: 'rgba(153, 102, 255, 1)',
            borderWidth: 1,
          }
        ];
      
        return <Bar data={{ labels: binLabels, datasets }} options={options} />;
      }
      

case 'pie':
  const pieLabels = chart_data.map((item) => item[visualization.label_column]); 
  console.log("pieLabels", pieLabels);
  console.log("chart_data", chart_data); 
  datasets = [
    {
      //label: chart_title, // Dataset label (optional, can be omitted if unnecessary)
      data: chart_data.map((item) => item[visualization.value_column]), // Values for each slice
      backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56'], // Colors for each slice
    }
    
  ];
  console.log(datasets);
  return <Pie data={{ labels: pieLabels, datasets }} options={options} />;
    default:
      return null;
  }
};



const getChartOptions = (type, chartTitle) => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 750,
    easing: 'easeInOutQuart',
  },
  plugins: {
    legend: {
      //display: type !== 'pie', 
      position: 'top', 
      labels: {
        boxWidth: 15,
        font: { size: 11 }
      }
    },
    title: {
      display: true,
      text: chartTitle,
      font: { size: 13 }
    },
  },

  scales: type === 'pie' ? undefined : {
    y: {
      beginAtZero: true,
      ticks: { 
        font: { size: 11 },
        callback: function(value) {
          return value.toLocaleString('id-ID');
        }
      }
    },
    x: {
      ticks: { 
        font: { size: 11 },
        maxRotation: 45,
        minRotation: 45
      }
    }
  },
  barPercentage: type === 'histogram' ? 1.0 : undefined,
  categoryPercentage: type === 'histogram' ? 1.0 : undefined
});



const formatDateLabel = (value, columnType) => {
  if (columnType.includes('month_year')|| columnType.includes('year_month')|| columnType.includes('bulan_tahun')|| columnType.includes('bulan')) {
    // If format is "2024_01"
    const [year, month] = value.split('_');
    return new Date(year, month - 1).toLocaleDateString('id-ID', { 
      month: 'short', 
      year: 'numeric' 
    });
  } else if (columnType.includes('month')) {
    // If format is "01"
    return new Date(2024, value - 1).toLocaleDateString('id-ID', { 
      month: 'long'
    });
  }
  return value; 
};

const sendMessage = async (e) => {
  e.preventDefault();
  const message = inputValue.trim();
  
  if (message && !isLoading) {
    setIsLoading(true);
    setInputValue('');
    setMessages(prev => [...prev, { role: 'user', content: message }]);

    if (!showVisualizations) {
      setIsExpanding(true);
      setTimeout(() => {
        setShowVisualizations(true);
        setIsExpanding(false);
      }, 300);
    }

    try {
      const response = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'bot', content: data.response }]);
      

      if (data.data && data.charts_info) {
        setRawData(data.data);
        setChartsInfo(data.charts_info);
        //const { x_column, y_column, chart_title } = data.tool_info.visualization;
        // const chartData = {
        //   labels: data.tool_info.chart_data.map(item => 
        //     formatDateLabel(item[x_column], x_column)
        //   ),
        //   datasets: [{
        //     label: y_column.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        //     data: data.tool_info.chart_data.map(item => item[y_column]),
        //     backgroundColor: data.tool_info.chart_data.map((_, index) => {
        //       const hue = (index * 360) / data.tool_info.chart_data.length;
        //       return `hsla(${hue}, 70%, 60%, 0.5)`;
        //     }),
        //     borderColor: data.tool_info.chart_data.map((_, index) => {
        //       const hue = (index * 360) / data.tool_info.chart_data.length;
        //       return `hsla(${hue}, 70%, 60%, 1)`;
        //     }),
        //     borderWidth: 1,
        //   }]
        // };
        
        //setBarData(chartData);
        //setChartTitle(chart_title);
        
        //processDataForVisualization(data.data);
      } else if (data.data && Array.isArray(data.data)) {
        // // Fallback to original process if no visualization info
        // processDataForVisualization(data.data);
      }

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'bot', 
        content: 'Sorry, there was an error processing your request.' 
      }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  }
};

const CURRENCY_COLUMNS = ['total_pagu', 'nilai', 'harga'];

const formatChartValue = (value, columnName) => {
  if (CURRENCY_COLUMNS.includes(columnName)) {
    return `Rp ${value.toLocaleString('id-ID')}`;
  }
  return value.toLocaleString('id-ID');
};

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 750,
      easing: 'easeInOutQuart',
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          boxWidth: 15,
          font: { size: 11 }
        }
      },
      title: {
        display: true,
        text: chartTitle,
        font: { size: 13 }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { 
          font: { size: 11 },
          callback: function(value) {
            return value.toLocaleString('id-ID');
          }
        }
      },
      x: {
        ticks: { 
          font: { size: 11 },
          maxRotation: 45,
          minRotation: 45
        }
      }
    },
  };

  return (
    <div className="flex min-h-screen bg-gray-50 p-4">
      <div className={`mx-auto transition-all duration-300 ease-in-out ${
        isExpanding ? 'scale-95 opacity-90' : ''
      } ${
        showVisualizations ? 'w-full' : 'w-2/3 max-w-3xl'
      }`}>
        {!showVisualizations ? (
          // Initial centered chat interface 
          <Card className="border-2 rounded-xl shadow-sm flex flex-col">
            <CardHeader className="border-b-2 bg-white rounded-t-xl py-3">
              <CardTitle>Data Analysis Assistant</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 p-0" ref={chatContainerRef}>
              <ScrollArea className="h-[calc(100vh-180px)]" >
                <div className="space-y-4 p-4 min-h-full flex flex-col">
                  <div className="flex-1">
                    {messages.map((message, index) => (
                      <div
                        key={index}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
                      >
                        <div
                          className={`max-w-[80%] rounded-xl p-3 shadow-sm ${
                            message.role === 'user'
                              ? 'bg-blue-500 text-white'
                              : 'bg-white border-2 border-gray-100'
                          }`}
                        >
                          {message.role === 'user' ? (
                            message.content
                          ) : (
                            <BotMessage content={message.content} />
                          )}
                        </div>
                      </div>
                    ))}
                    {isLoading && <LoadingMessage />}
                  </div>
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
            </CardContent>
            <CardFooter className="border-t-2 bg-white rounded-b-xl p-3">
              <form onSubmit={sendMessage} className="flex w-full gap-2">
                <Button 
                  variant="outline" 
                  size="icon" 
                  className="border-2"
                  disabled={isLoading}
                >
                  <Plus className="h-4 w-4" />
                </Button>
                <Input
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder={isLoading ? "Processing..." : "Type anything to generate analysis..."}
                  className="flex-1 border-2"
                  disabled={isLoading}
                />
                <Button 
                  type="submit" 
                  size="icon" 
                  className="border-2"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>
            </CardFooter>
          </Card>
        ) : (
          // New  layout
          <div className="flex flex-col h-screen gap-4">
            {/* Main Content  */}
            <div className="flex gap-4 flex-1">
              {/* Charts Section - Center */}
              <div className="flex-1">
                <ScrollArea className="h-[calc(100vh-300px)]">
                  <Card className="border-2 rounded-xl shadow-sm">
                    <CardHeader className="border-b-2 bg-white rounded-t-xl py-2">
                      <CardTitle className="text-sm">Chart Section</CardTitle>
                    </CardHeader>
                    <CardContent className="p-3">
                      <div className="space-y-3">
                        {isLoading ? (
                          <div className="flex flex-col items-center justify-center gap-2 p-8">
                            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                            <p className="text-sm text-gray-500">Preparing visualization...</p>
                          </div>
                        ) : chartsInfo.length > 0 ? (
                          <div className="grid gap-4" style={{ 
                            gridTemplateColumns: `repeat(2, 1fr)`, // Set to 2 columns for 2x2 grid layout
                            gridTemplateRows: `repeat(${Math.ceil(chartsInfo.length / 2)}, 1fr)`, // Adjust rows based on the number of charts
                          }}>
                            {chartsInfo.slice(0, 4).map((chart, index) => ( // Limit to maximum of 4 charts
                              <div key={index} className="border rounded shadow-sm p-2">
                                <CardHeader className="border-b-2 bg-white rounded-t-xl py-1">
                                  <CardTitle className="text-xs">{chart.visualization.chart_title}</CardTitle>
                                </CardHeader>
                                <CardContent className="p-2">
                                  <div className="h-[250px]">
                                    {renderChart(chart)}
                                  </div>
                                </CardContent>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-center text-gray-500">No charts available</p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </ScrollArea>
              </div>
                
              {/* Raw Data Table - right side */}
              <div className="w-1/3">
                <Card className="border-2 rounded-xl shadow-sm">
                  <CardHeader className="border-b-2 bg-white rounded-t-xl py-2">
                    <CardTitle className="text-sm">Raw Data</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {rawData ? (
                      <div className="h-[calc(100vh-300px)] overflow-auto">
                        <table className="w-full text-left text-sm">
                          <thead className="bg-gray-50 border-b-2 sticky top-0">
                            <tr>
                              {Object.keys(rawData[0])
                                .filter(column => !EXCLUDED_COLUMNS.includes(column))
                                .map((column, index) => (
                                  <th key={index} className="p-2 whitespace-nowrap bg-gray-50">
                                    {column.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                  </th>
                                ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y-2">
                            {rawData.map((row, rowIndex) => (
                              <tr key={rowIndex} className="bg-white">
                                {Object.entries(row)
                                  .filter(([key]) => !EXCLUDED_COLUMNS.includes(key))
                                  .map(([columnName, value], colIndex) => (
                                    <td key={colIndex} className="p-2 whitespace-nowrap">
                                      {formatValue(value, columnName)}
                                    </td>
                                  ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : isLoading && (
                      <div className="h-[calc(100vh-300px)] flex items-center justify-center">
                        <div className="flex flex-col items-center gap-2">
                          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                          <p className="text-sm text-gray-500">Loading data...</p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
  
            {/* Chat Interface - Bottom */}
            <div className="h-[250px]">
              <Card className="border-2 rounded-xl shadow-sm h-full">
                <CardHeader className="border-b-2 bg-white rounded-t-xl py-2">
                  <CardTitle>Data Analysis Assistant</CardTitle>
                </CardHeader>
                <CardContent className="flex-1 p-0" ref={chatContainerRef}>
                  <ScrollArea className="h-[calc(250px-120px)]">
                    <div className="space-y-4 p-4 min-h-full flex flex-col">
                      <div className="flex-1">
                        {messages.map((message, index) => (
                          <div
                            key={index}
                            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
                          >
                            <div
                              className={`max-w-[80%] rounded-xl p-3 shadow-sm ${
                                message.role === 'user'
                                  ? 'bg-blue-500 text-white'
                                  : 'bg-white border-2 border-gray-100'
                              }`}
                            >
                              {message.role === 'user' ? (
                                message.content
                              ) : (
                                <BotMessage content={message.content} />
                              )}
                            </div>
                          </div>
                        ))}
                        {isLoading && <LoadingMessage />}
                      </div>
                      <div ref={messagesEndRef} />
                    </div>
                  </ScrollArea>
                </CardContent>
                <CardFooter className="border-t-2 bg-white rounded-b-xl p-3">
                  <form onSubmit={sendMessage} className="flex w-full gap-2">
                    <Button 
                      variant="outline" 
                      size="icon" 
                      className="border-2"
                      disabled={isLoading}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                    <Input
                      ref={inputRef}
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder={isLoading ? "Processing..." : "Type anything to generate analysis..."}
                      className="flex-1 border-2"
                      disabled={isLoading}
                    />
                    <Button 
                      type="submit" 
                      size="icon" 
                      className="border-2"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                  </form>
                </CardFooter>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatbotInterface;