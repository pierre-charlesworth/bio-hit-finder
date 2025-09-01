import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';

const Contact = () => {
  return (
    <section id="contact" className="py-24 bg-muted/30">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
          <div>
            <h2 className="text-fluid-xl font-light tracking-tight mb-8">
              Let's start a{' '}
              <span className="font-medium">conversation</span>
            </h2>
            
            <p className="text-muted-foreground text-lg mb-12 leading-relaxed">
              Have a project in mind? We'd love to hear about it. 
              Drop us a line and we'll get back to you within 24 hours.
            </p>
            
            <div className="space-y-6">
              <div>
                <h3 className="font-medium mb-2">Email</h3>
                <p className="text-muted-foreground">hello@studio.com</p>
              </div>
              
              <div>
                <h3 className="font-medium mb-2">Phone</h3>
                <p className="text-muted-foreground">+1 (555) 123-4567</p>
              </div>
              
              <div>
                <h3 className="font-medium mb-2">Location</h3>
                <p className="text-muted-foreground">
                  San Francisco, CA<br />
                  New York, NY
                </p>
              </div>
            </div>
          </div>
          
          <Card className="p-8 border-0 shadow-none bg-background">
            <form className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="name" className="text-sm font-medium mb-2 block">
                    Name
                  </label>
                  <Input id="name" placeholder="Your name" />
                </div>
                
                <div>
                  <label htmlFor="email" className="text-sm font-medium mb-2 block">
                    Email
                  </label>
                  <Input id="email" type="email" placeholder="your@email.com" />
                </div>
              </div>
              
              <div>
                <label htmlFor="subject" className="text-sm font-medium mb-2 block">
                  Subject
                </label>
                <Input id="subject" placeholder="Project inquiry" />
              </div>
              
              <div>
                <label htmlFor="message" className="text-sm font-medium mb-2 block">
                  Message
                </label>
                <Textarea 
                  id="message" 
                  placeholder="Tell us about your project..."
                  rows={6}
                />
              </div>
              
              <Button size="lg" className="w-full">
                Send Message
              </Button>
            </form>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default Contact;