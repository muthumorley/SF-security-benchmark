public with sharing class InvoiceApprovalController {
    @AuraEnabled
    public static void approveInvoice(Id invoiceId) {
        Invoice__c inv = [SELECT Id, Status__c FROM Invoice__c
                          WHERE Id = :invoiceId WITH USER_MODE];
        inv.Status__c = 'Approved';
        update as user inv;
    }

    @AuraEnabled(cacheable=true)
    public static List<Invoice__c> getPendingInvoices() {
        return [SELECT Id, Name, Amount__c, Status__c, Vendor__c
                FROM Invoice__c
                WHERE Status__c = 'Pending'
                WITH USER_MODE LIMIT 100];
    }
}
