import React from 'react';
import { Printer, Clock, Truck, FileCheck, AlertTriangle, CheckCircle, Package } from 'lucide-react';

const PrintingInfoPage = () => {
  const faqs = [
    {
      question: "What types of printing do you offer?",
      answer: (
        <ul className="list-disc pl-5 space-y-1">
          <li><strong>DTF printing</strong> for apparel (1+ items)</li>
          <li><strong>Screen printing</strong> for apparel (7+ items)</li>
          <li><strong>UV DTF printing</strong> for mugs and drinkware (1+ items)</li>
        </ul>
      ),
      note: "Each printing method is selected to ensure the best quality based on the product and order size."
    },
    {
      question: "What are your minimum quantities?",
      answer: (
        <ul className="list-disc pl-5 space-y-1">
          <li><strong>DTF Apparel:</strong> 1+</li>
          <li><strong>Screen Printing:</strong> 7+</li>
          <li><strong>UV DTF (Mugs & Drinkware):</strong> 1+</li>
        </ul>
      ),
      note: "These minimums apply to custom orders only."
    },
    {
      question: "Do you sell your own designs?",
      answer: (
        <div>
          <p className="mb-2">Yes. We offer a lineup of Christian-designed retail products, including:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>T-shirts</li>
            <li>Hoodies</li>
            <li>Hats</li>
            <li>Mugs</li>
          </ul>
        </div>
      ),
      note: "These items feature our original designs, are sold at retail pricing, and cannot be customized."
    },
    {
      question: "What is your turnaround time?",
      answer: (
        <ul className="list-disc pl-5 space-y-1">
          <li><strong>Custom Orders (DTF or Screen Print):</strong> 3–10 business days</li>
          <li><strong>Designed Products:</strong> 24-hour turnaround</li>
        </ul>
      ),
      note: "Turnaround time depends on the printing method and order volume."
    },
    {
      question: "Do you offer free shipping?",
      answer: (
        <div className="space-y-3">
          <div>
            <p className="font-semibold">Designed Products:</p>
            <ul className="list-disc pl-5">
              <li>Free shipping on orders $75+</li>
              <li>Shipping applies under $75</li>
            </ul>
          </div>
          <div>
            <p className="font-semibold">Custom Orders:</p>
            <ul className="list-disc pl-5">
              <li>Shipping fees always apply</li>
            </ul>
          </div>
        </div>
      )
    },
    {
      question: "What is required for custom printing?",
      answer: "Customers must provide high-resolution, print-ready artwork suitable for apparel or drinkware printing.",
      note: "We print exactly what is submitted."
    },
    {
      question: "Do you offer custom design services?",
      answer: "Generally, no. We do not create or redesign artwork. We may adjust print size only if required for production, but we do not fix spelling errors, layout issues, or design mistakes."
    },
    {
      question: "Can you fix errors in my design?",
      answer: (
        <div>
          <p className="mb-2">We can adjust sizing if necessary, but:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>We do not correct spelling</li>
            <li>We do not redesign artwork</li>
            <li>We do not fix layout or content errors</li>
          </ul>
        </div>
      ),
      note: "Responsibility for the design rests entirely with the customer."
    }
  ];

  const printingMethods = [
    { method: "DTF Apparel", minimum: "1+" },
    { method: "Screen Printing", minimum: "7+" },
    { method: "UV DTF (Mugs & Drinkware)", minimum: "1+" }
  ];

  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="font-heading text-4xl md:text-5xl font-bold mb-4">Printing & Ordering Information</h1>
          <p className="text-lg text-muted-foreground">Everything you need to know about our printing services</p>
        </div>

        {/* FAQ Section */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <Printer className="h-6 w-6 text-primary" />
            <h2 className="font-heading text-2xl font-bold">Frequently Asked Questions</h2>
          </div>
          <div className="space-y-6">
            {faqs.map((faq, index) => (
              <div key={index} className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
                <h3 className="font-heading font-bold text-lg mb-3">{faq.question}</h3>
                <div className="text-muted-foreground">
                  {typeof faq.answer === 'string' ? <p>{faq.answer}</p> : faq.answer}
                </div>
                {faq.note && (
                  <p className="mt-3 text-sm italic text-muted-foreground border-l-2 border-primary pl-3">
                    {faq.note}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Quick Reference */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <Package className="h-6 w-6 text-accent" />
            <h2 className="font-heading text-2xl font-bold">Printing Methods & Minimums</h2>
          </div>
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-4 font-heading">Method</th>
                  <th className="text-right p-4 font-heading">Minimum Quantity</th>
                </tr>
              </thead>
              <tbody>
                {printingMethods.map((item, index) => (
                  <tr key={index} className="border-t">
                    <td className="p-4 font-medium">{item.method}</td>
                    <td className="p-4 text-right font-bold text-primary">{item.minimum}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Turnaround Times */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <Clock className="h-6 w-6 text-secondary" />
            <h2 className="font-heading text-2xl font-bold">Turnaround Times</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
              <h3 className="font-heading font-bold mb-2">Custom Orders</h3>
              <p className="text-3xl font-bold text-primary">3–10 days</p>
              <p className="text-sm text-muted-foreground">Business days, depending on method</p>
            </div>
            <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
              <h3 className="font-heading font-bold mb-2">Designed Products</h3>
              <p className="text-3xl font-bold text-accent">24 hours</p>
              <p className="text-sm text-muted-foreground">Our original designs ship fast</p>
            </div>
          </div>
        </div>

        {/* Shipping Info */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <Truck className="h-6 w-6 text-chart-4" />
            <h2 className="font-heading text-2xl font-bold">Shipping Policy</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-green-50 border-2 border-green-400 rounded-xl p-6">
              <h3 className="font-heading font-bold mb-2 text-green-800">Designed Products</h3>
              <ul className="space-y-2 text-green-700">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4" />
                  Free shipping on orders $75+
                </li>
                <li className="flex items-center gap-2">
                  <Truck className="h-4 w-4" />
                  Shipping fee under $75
                </li>
              </ul>
            </div>
            <div className="bg-yellow-50 border-2 border-yellow-400 rounded-xl p-6">
              <h3 className="font-heading font-bold mb-2 text-yellow-800">Custom Orders</h3>
              <ul className="space-y-2 text-yellow-700">
                <li className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Shipping fees always apply
                </li>
                <li className="flex items-center gap-2">
                  <FileCheck className="h-4 w-4" />
                  Regardless of order total
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="bg-red-50 border-2 border-red-300 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-red-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-heading font-bold text-red-800 mb-2">Important Disclaimer</h3>
              <p className="text-red-700 text-sm">
                Revolution Printing is not responsible for errors, omissions, or defects present in customer-provided artwork. 
                By submitting an order, the customer confirms that all files are approved for production and accepts full 
                responsibility for the final printed result.
              </p>
            </div>
          </div>
        </div>

        {/* By Placing Order Agreement */}
        <div className="mt-8 bg-white border-2 border-black rounded-xl shadow-brutal p-6">
          <h3 className="font-heading font-bold text-lg mb-4">📌 By Placing an Order, You Agree That:</h3>
          <ul className="space-y-2 text-muted-foreground">
            <li className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
              You have reviewed and approved your artwork before submission
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
              You accept full responsibility for the content, spelling, and layout of your design
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
              Revolution Printing is not responsible for errors in customer-supplied artwork
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
              Custom orders are printed exactly as provided
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
              Turnaround times and shipping policies are clearly understood
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PrintingInfoPage;
