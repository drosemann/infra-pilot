# code review assistant

## description

a comprehensive code review prompt that analyzes code quality, identifies potential issues, suggests improvements, and provides detailed feedback on best practices, security, performance, and maintainability.

## usage

paste your code along with any specific concerns or focus areas. works with any programming language. best used for reviewing pull requests, refactoring decisions, or general code quality assessment.

## prompt

```markdown
Please perform a comprehensive code review of the following code. Analyze it for:

1. **Code Quality & Style**
   - Readability and clarity
   - Naming conventions
   - Code organization and structure
   - Adherence to language-specific best practices

2. **Performance & Efficiency**
   - Algorithm efficiency
   - Resource usage
   - Potential bottlenecks
   - Optimization opportunities

3. **Security Concerns**
   - Potential vulnerabilities
   - Input validation
   - Data handling practices
   - Security best practices

4. **Maintainability**
   - Code complexity
   - Documentation and comments
   - Modularity and reusability
   - Error handling

5. **Testing & Reliability**
   - Edge cases consideration
   - Error scenarios
   - Testing recommendations

Please provide:
- Specific line-by-line feedback where applicable
- Priority levels for each issue (Critical/High/Medium/Low)
- Concrete suggestions for improvement
- Positive aspects worth highlighting

Code to review:
```

[YOUR CODE HERE]

```

Additional context or specific concerns:
[SPECIFY ANY PARTICULAR AREAS TO FOCUS ON]
```

## example input

```markdown
```javascript
function calculateDiscount(price, discountPercent) {
    var discount = price * discountPercent / 100;
    var finalPrice = price - discount;
    return finalPrice;
}

function processOrder(items) {
    var total = 0;
    for(var i = 0; i < items.length; i++) {
        total += calculateDiscount(items[i].price, items[i].discount);
    }
    return total;
}
```

```

## example output

```markdown
## Code Review Feedback

### Overall Assessment
The code is functional but has several areas for improvement in terms of best practices, error handling, and modern JavaScript conventions.

### Specific Issues

**Medium Priority Issues:**
1. **Line 1-4**: Use `const`/`let` instead of `var` for better scoping
2. **Line 1**: Missing input validation - function should handle edge cases
3. **Line 6-10**: Consider using modern array methods like `reduce()`

**Low Priority Issues:**
1. **General**: Add JSDoc comments for better documentation
2. **Line 6**: Variable naming could be more descriptive

### Suggested Improvements

```javascript
/**
 * Calculates discounted price
 * @param {number} price - Original price (must be positive)
 * @param {number} discountPercent - Discount percentage (0-100)
 * @returns {number} Final price after discount
 */
function calculateDiscount(price, discountPercent) {
    if (price < 0 || discountPercent < 0 || discountPercent > 100) {
        throw new Error('Invalid input parameters');
    }
    
    const discount = price * discountPercent / 100;
    return price - discount;
}

/**
 * Calculates total for order with individual item discounts
 * @param {Array} items - Array of items with price and discount properties
 * @returns {number} Total order amount
 */
function processOrder(items) {
    if (!Array.isArray(items)) {
        throw new Error('Items must be an array');
    }
    
    return items.reduce((total, item) => {
        return total + calculateDiscount(item.price, item.discount);
    }, 0);
}
```

### Positive Aspects

- Clear function naming that describes purpose
- Simple, focused functions following single responsibility principle
- Clean separation between discount calculation and order processing

```

## variations

• security-focused: emphasize security vulnerabilities and data protection
• performance-focused: concentrate on optimization and efficiency
• junior developer: provide more educational explanations and learning resources
• legacy code: focus on modernization and technical debt reduction

## tips

• provide the programming language for more targeted feedback
• include context about the application domain for better security analysis
• mention any specific coding standards or frameworks being used
• be specific about performance requirements or constraints

## related prompts

• `refactoring-assistant.md` - for code improvement suggestions
• `documentation-generator.md` - for adding comprehensive documentation
• `test-case-generator.md` - for creating tests for reviewed code

## tags

`code-review` `quality-assurance` `best-practices` `development` `debugging`
