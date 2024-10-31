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
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement } from 'chart.js';
import { Bar } from 'react-chartjs-2';
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
  
  const messagesEndRef = useRef(null);
  const scrollAreaRef = useRef(null);
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


const processDataForVisualization = (data) => {
  if (!data || !Array.isArray(data) || data.length === 0) return;

  setRawData(data);


  const columns = Object.keys(data[0]);
  

  const numericColumns = columns.filter(col => {
    const value = data[0][col];
    return isNumeric(value) && 
           !['id', '_id', 'kode_rup'].includes(col) && 
           data.some(row => Number(row[col]) > 0); 
  });

  const stringColumns = columns.filter(col => 
    typeof data[0][col] === 'string' &&
    !['filtered_keywords', 'uraian_pekerjaan', 'spesifikasi_pekerjaan'].includes(col) && 
    data.some(row => row[col]?.trim().length > 0) 
  );

  // Choose the best columns for visualization
  const valueColumn = numericColumns.find(col => 
    col.toLowerCase().includes('total') ||
    col.toLowerCase().includes('pagu') ||
    col.toLowerCase().includes('nilai')
  ) || numericColumns[0];

  const labelColumn = stringColumns.find(col =>
    col.toLowerCase().includes('nama') ||
    col.toLowerCase().includes('satuan_kerja') ||
    col.toLowerCase().includes('title')
  ) || stringColumns[0];

  if (valueColumn && labelColumn) {

    const aggregatedData = data.reduce((acc, curr) => {
      const label = curr[labelColumn];
      if (!acc[label]) {
        acc[label] = 0;
      }
      acc[label] += Number(curr[valueColumn]);
      return acc;
    }, {});

    const barChartData = {
      labels: Object.keys(aggregatedData),
      datasets: [{
        label: valueColumn.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        data: Object.values(aggregatedData),
        backgroundColor: Object.keys(aggregatedData).map((_, index) => {
          const hue = (index * 360) / Object.keys(aggregatedData).length;
          return `hsla(${hue}, 70%, 60%, 0.5)`;
        }),
        borderColor: Object.keys(aggregatedData).map((_, index) => {
          const hue = (index * 360) / Object.keys(aggregatedData).length;
          return `hsla(${hue}, 70%, 60%, 1)`;
        }),
        borderWidth: 1,
      }]
    };

    setChartTitle(`${valueColumn.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} by ${labelColumn.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`);
    setBarData(barChartData);
  }
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
      

      if (data.data && data.tool_info?.visualization) {
        const { x_column, y_column, chart_title } = data.tool_info.visualization;
        console.log(data.tool_info.visualization);
        const chartData = {
          labels: data.data.map(item => item[x_column]),
          datasets: [{
            label: y_column.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            data: data.data.map(item => item[y_column]),
            backgroundColor: data.data.map((_, index) => {
              const hue = (index * 360) / data.data.length;
              return `hsla(${hue}, 70%, 60%, 0.5)`;
            }),
            borderColor: data.data.map((_, index) => {
              const hue = (index * 360) / data.data.length;
              return `hsla(${hue}, 70%, 60%, 1)`;
            }),
            borderWidth: 1,
          }]
        };
        
        setBarData(chartData);
        setChartTitle(chart_title);
        setRawData(data.data);
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
        <div className={`flex gap-4 transition-all duration-300 ${
          showVisualizations ? 'opacity-100' : 'opacity-100'
        }`}>
          {/* Chat Interface */}
          <Card className={`border-2 rounded-xl shadow-sm flex flex-col transition-all duration-300 ${
            showVisualizations ? 'w-1/2' : 'w-full'
          }`}>
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

          {/* Visualizations Panel */}
          {showVisualizations && (
            <div className="w-1/2 flex flex-col gap-3 transition-all duration-300">
              <ScrollArea className="h-[calc(100vh-32px)]">
                <div className="space-y-3 p-1">
                  {barData ? (
                    <Card className="border-2 rounded-xl shadow-sm">
                      <CardHeader className="border-b-2 bg-white rounded-t-xl py-2">
                        <CardTitle className="text-sm">{chartTitle}</CardTitle>
                      </CardHeader>
                      <CardContent className="p-3">
                        <div className="h-[300px]">
                          <Bar data={barData} options={chartOptions} />
                        </div>
                      </CardContent>
                    </Card>
                  ) : isLoading && showVisualizations && (
                    <Card className="border-2 rounded-xl shadow-sm p-8">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                        <p className="text-sm text-gray-500">Preparing visualization...</p>
                      </div>
                    </Card>
                  )}

                  {/* Raw Data Table */}
                  {rawData ? (
                  <Card className="border-2 rounded-xl shadow-sm">
                    <CardHeader className="border-b-2 bg-white rounded-t-xl py-2">
                      <CardTitle className="text-sm">Raw Data</CardTitle>
                    </CardHeader>
                    <CardContent className="p-0">
                      <div className="h-[400px] overflow-auto"> {/* Fixed height */}
                        <table className="w-full text-left text-sm">
                          <thead className="bg-gray-50 border-b-2 sticky top-0"> {/* Make header sticky */}
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
                    </CardContent>
                  </Card>
                ) : isLoading && showVisualizations && (
                  <Card className="border-2 rounded-xl shadow-sm p-8 h-[400px]">
                    <div className="flex flex-col items-center justify-center gap-2 h-full">
                      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                      <p className="text-sm text-gray-500">Loading data...</p>
                    </div>
                  </Card>
                )}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatbotInterface;