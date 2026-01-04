import React from 'react';
import { Printer, Clock, Truck, FileCheck, AlertTriangle, CheckCircle, Package, Upload, RefreshCw, FileText, Shield, ChevronDown } from 'lucide-react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const PrintingInfoPage = () => {
  return (
    <div className="min-h-screen bg-background py-12">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="font-heading text-4xl md:text-5xl font-bold mb-4">Policies, Printing Info & Terms</h1>
          <p className="text-lg text-muted-foreground">Revolution Printing</p>
        </div>

        {/* Quick Overview */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Printer className="h-6 w-6 text-primary" />
            <h2 className="font-heading text-2xl font-bold">Printing Services (Quick Overview)</h2>
          </div>
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal overflow-hidden">
            <table className="w-full">
              <tbody>
                <tr className="border-b">
                  <td className="p-4 font-medium">DTF Printing (Apparel)</td>
                  <td className="p-4 text-right font-bold text-primary">1+ items</td>
                </tr>
                <tr className="border-b">
                  <td className="p-4 font-medium">Screen Printing (Apparel)</td>
                  <td className="p-4 text-right font-bold text-primary">7+ items</td>
                </tr>
                <tr>
                  <td className="p-4 font-medium">UV DTF Printing (Mugs & Drinkware)</td>
                  <td className="p-4 text-right font-bold text-primary">1+ items</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Designed Products */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Package className="h-6 w-6 text-accent" />
            <h2 className="font-heading text-2xl font-bold">Designed Christian Products (Retail Line)</h2>
          </div>
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
            <p className="mb-4">We sell our own line of Christian apparel and drinkware, including:</p>
            <ul className="list-disc pl-6 mb-4 space-y-1">
              <li>T-shirts</li>
              <li>Hoodies</li>
              <li>Hats</li>
              <li>Mugs</li>
            </ul>
            <p className="text-muted-foreground italic mb-4">
              These products feature our original designs, are sold at retail pricing, and are not customizable.
            </p>
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="bg-green-50 border border-green-300 rounded-lg p-4 text-center">
                <Clock className="h-6 w-6 text-green-600 mx-auto mb-2" />
                <p className="font-bold text-green-800">Turnaround: 24 hours</p>
              </div>
              <div className="bg-green-50 border border-green-300 rounded-lg p-4 text-center">
                <Truck className="h-6 w-6 text-green-600 mx-auto mb-2" />
                <p className="font-bold text-green-800">Free Shipping: $75+</p>
                <p className="text-xs text-green-700">Shipping applies under $75</p>
              </div>
            </div>
          </div>
        </div>

        {/* Custom Order Turnaround */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Clock className="h-6 w-6 text-secondary" />
            <h2 className="font-heading text-2xl font-bold">Custom Order Turnaround Time</h2>
          </div>
          <div className="bg-yellow-50 border-2 border-yellow-400 rounded-xl p-6">
            <p className="font-medium text-yellow-800">
              <strong>DTF & Screen Printed Custom Orders:</strong><br />
              3–10 business days (depending on method and order volume)
            </p>
          </div>
        </div>

        {/* Artwork Upload Instructions */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Upload className="h-6 w-6 text-chart-4" />
            <h2 className="font-heading text-2xl font-bold">📤 Custom Artwork Upload Instructions</h2>
          </div>
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
            <h3 className="font-heading font-bold mb-3">Artwork Requirements</h3>
            <ul className="list-disc pl-6 mb-6 space-y-2 text-muted-foreground">
              <li>High-resolution files only (300 DPI recommended)</li>
              <li>Print-ready artwork for apparel or drinkware</li>
              <li>Accepted formats: <strong>PNG, SVG, PDF, high-resolution JPG</strong></li>
              <li>Transparent background preferred for apparel</li>
            </ul>
            
            <div className="bg-red-50 border border-red-300 rounded-lg p-4">
              <h4 className="font-bold text-red-800 mb-2">⚠️ Important</h4>
              <ul className="list-disc pl-6 space-y-1 text-red-700 text-sm">
                <li>We do not offer custom design services</li>
                <li>We do not fix spelling, grammar, or layout errors</li>
                <li>We print exactly what is submitted</li>
                <li>We may adjust print size only if required for production</li>
              </ul>
              <p className="mt-3 text-red-800 font-medium text-sm">
                By uploading artwork, you confirm it is final and approved for printing.
              </p>
            </div>
          </div>
        </div>

        {/* Accordions for Policies */}
        <div className="mb-8">
          <Accordion type="multiple" className="space-y-4">
            
            {/* Refund Policy */}
            <AccordionItem value="refunds" className="bg-white border-2 border-black rounded-xl shadow-brutal overflow-hidden">
              <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-muted/50">
                <div className="flex items-center gap-3">
                  <RefreshCw className="h-5 w-5 text-primary" />
                  <span className="font-heading font-bold text-lg">🔁 Refund Policy</span>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-6 pb-6">
                <p className="font-medium mb-4 text-red-600">
                  Due to the custom nature of our products, all sales are final.
                </p>
                
                <h4 className="font-bold mb-2">Refunds or Reprints</h4>
                <p className="text-muted-foreground mb-2">
                  Refunds or reprints are issued only if a defect is caused by us as the printer.
                </p>
                <p className="text-muted-foreground mb-4">
                  Examples include printing errors, incorrect products, or manufacturing defects.
                </p>
                
                <h4 className="font-bold mb-2">Not Considered Defects</h4>
                <ul className="list-disc pl-6 space-y-1 text-muted-foreground mb-4">
                  <li>Spelling or design errors in customer-supplied artwork</li>
                  <li>Artwork quality issues</li>
                  <li>Colour differences between screen and print</li>
                  <li>Placement or sizing consistent with submitted artwork</li>
                </ul>
                
                <p className="text-sm bg-yellow-50 border border-yellow-300 rounded-lg p-3 text-yellow-800">
                  All claims must be submitted within <strong>48 hours</strong> of delivery with clear photos.
                </p>
              </AccordionContent>
            </AccordionItem>

            {/* Shipping Policy */}
            <AccordionItem value="shipping" className="bg-white border-2 border-black rounded-xl shadow-brutal overflow-hidden">
              <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-muted/50">
                <div className="flex items-center gap-3">
                  <Truck className="h-5 w-5 text-accent" />
                  <span className="font-heading font-bold text-lg">🚚 Shipping Policy</span>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-6 pb-6">
                <div className="grid md:grid-cols-2 gap-4 mb-4">
                  <div className="bg-green-50 border border-green-300 rounded-lg p-4">
                    <h4 className="font-bold text-green-800 mb-2">Designed Products</h4>
                    <ul className="space-y-1 text-green-700 text-sm">
                      <li>✓ Free shipping on orders $75+</li>
                      <li>• Shipping applies under $75</li>
                    </ul>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4">
                    <h4 className="font-bold text-yellow-800 mb-2">Custom Orders</h4>
                    <ul className="space-y-1 text-yellow-700 text-sm">
                      <li>• Shipping fees always apply</li>
                    </ul>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  Revolution Printing is not responsible for carrier delays.
                </p>
              </AccordionContent>
            </AccordionItem>

            {/* Terms & Conditions */}
            <AccordionItem value="terms" className="bg-white border-2 border-black rounded-xl shadow-brutal overflow-hidden">
              <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-muted/50">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-secondary" />
                  <span className="font-heading font-bold text-lg">📄 Terms & Conditions</span>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-6 pb-6">
                <h4 className="font-bold mb-2">General</h4>
                <ul className="list-disc pl-6 space-y-1 text-muted-foreground mb-4">
                  <li>All items are made to order</li>
                  <li>Orders cannot be canceled once production begins</li>
                  <li>Turnaround times are estimates, not guarantees</li>
                </ul>
                
                <h4 className="font-bold mb-2">Artwork Responsibility</h4>
                <ul className="list-disc pl-6 space-y-1 text-muted-foreground mb-4">
                  <li>Customers are fully responsible for submitted artwork</li>
                  <li>Minor colour variation may occur due to printing processes</li>
                </ul>
                
                <h4 className="font-bold mb-2">Liability</h4>
                <ul className="list-disc pl-6 space-y-1 text-muted-foreground">
                  <li>Liability is limited to replacement of defective items only</li>
                  <li>No refunds for customer-supplied artwork errors</li>
                  <li>No responsibility for delays beyond our control</li>
                </ul>
              </AccordionContent>
            </AccordionItem>

          </Accordion>
        </div>

        {/* Order Confirmation */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-6">
            <CheckCircle className="h-6 w-6 text-green-600" />
            <h2 className="font-heading text-2xl font-bold">✅ Order Confirmation (Required)</h2>
          </div>
          <div className="bg-white border-2 border-black rounded-xl shadow-brutal p-6">
            <p className="text-muted-foreground mb-4">
              Before placing an order, customers must confirm:
            </p>
            <ul className="space-y-2 text-sm">
              <li className="flex items-start gap-2">
                <span className="text-muted-foreground">☐</span>
                <span>I confirm my artwork is print-ready and high-resolution</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-muted-foreground">☐</span>
                <span>I understand Revolution Printing does not provide design services</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-muted-foreground">☐</span>
                <span>I accept responsibility for spelling, layout, and content</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-muted-foreground">☐</span>
                <span>I understand only print size may be adjusted</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-muted-foreground">☐</span>
                <span>I understand custom orders take 3–10 business days</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-muted-foreground">☐</span>
                <span>I understand shipping always applies to custom orders</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-muted-foreground">☐</span>
                <span>I understand designed products are not customizable</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-muted-foreground">☐</span>
                <span>I understand refund eligibility is limited to printer-caused defects only</span>
              </li>
            </ul>
          </div>
        </div>

        {/* By Placing Order */}
        <div className="mb-8">
          <div className="bg-primary/10 border-2 border-primary rounded-xl p-6">
            <h3 className="font-heading font-bold text-lg mb-4">📌 By Placing an Order, You Agree That:</h3>
            <ul className="space-y-2 text-muted-foreground">
              <li className="flex items-start gap-2">
                <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                Your artwork is final and approved
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                You accept responsibility for the final printed result
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                Revolution Printing is not liable for artwork errors
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-5 w-5 text-primary flex-shrink-0 mt-0.5" />
                Policies, turnaround times, and shipping terms are understood
              </li>
            </ul>
          </div>
        </div>

        {/* Canadian Consumer Notice */}
        <div className="mb-8">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <span className="text-2xl">🇨🇦</span>
              <div>
                <h3 className="font-heading font-bold text-red-800 mb-2">Canadian Consumer Notice</h3>
                <p className="text-red-700 text-sm">
                  Nothing in these terms limits your rights under applicable Canadian consumer protection laws. 
                  Where required by law, statutory consumer rights apply.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Legal Disclaimer */}
        <div className="bg-gray-100 border-2 border-gray-300 rounded-xl p-6">
          <div className="flex items-start gap-3">
            <Shield className="h-6 w-6 text-gray-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-heading font-bold text-gray-800 mb-2">⚖️ Legal Disclaimer</h3>
              <p className="text-gray-600 text-sm">
                Revolution Printing prints customer-provided artwork as submitted and is not responsible for 
                errors, omissions, or design flaws contained within supplied files.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrintingInfoPage;
